suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(ggplot2)
  library(scales)
})

set.seed(2026)

data_dir <- "dataset"
output_dir <- "output"
data_output_dir <- file.path(output_dir, "data")
table_output_dir <- file.path(output_dir, "tables")
figure_output_dir <- file.path(output_dir, "figures")
dir.create(data_output_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(table_output_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figure_output_dir, recursive = TRUE, showWarnings = FALSE)

team_name_map <- c(
  "Delhi Daredevils" = "Delhi Capitals",
  "Kings XI Punjab" = "Punjab Kings",
  "Rising Pune Supergiants" = "Rising Pune Supergiant",
  "Royal Challengers Bangalore" = "Royal Challengers Bengaluru"
)

standardize_team <- function(team) {
  replacement <- unname(team_name_map[team])
  ifelse(is.na(replacement), team, replacement)
}

scalar_or_na <- function(x) {
  if (is.null(x) || length(x) == 0) NA_character_ else as.character(x[[1]])
}

count_wickets <- function(deliveries) {
  sum(vapply(deliveries, function(delivery) {
    wickets <- delivery$wickets
    if (is.null(wickets) || length(wickets) == 0) return(0L)
    sum(vapply(wickets, function(wicket) {
      !identical(scalar_or_na(wicket$kind), "retired hurt")
    }, logical(1)))
  }, integer(1)))
}

count_legal_balls <- function(deliveries) {
  sum(vapply(deliveries, function(delivery) {
    extras <- delivery$extras
    is_wide <- !is.null(extras$wides)
    is_no_ball <- !is.null(extras$noballs)
    !(is_wide || is_no_ball)
  }, logical(1)))
}

parse_match <- function(path) {
  match <- fromJSON(path, simplifyVector = FALSE)
  info <- match$info
  outcome <- info$outcome
  result <- scalar_or_na(outcome$result)
  winner <- scalar_or_na(outcome$winner)
  if (is.na(winner) && identical(result, "tie")) {
    winner <- scalar_or_na(outcome$eliminator)
  }

  # No-result/abandoned games cannot produce a binary response.
  if (is.na(winner)) return(NULL)

  teams <- vapply(info$teams, as.character, character(1))
  loser <- setdiff(teams, winner)
  if (length(teams) != 2 || length(loser) != 1) return(NULL)

  season_raw <- scalar_or_na(info$season)
  season <- suppressWarnings(as.integer(substr(season_raw, 1, 4)))
  match_id <- tools::file_path_sans_ext(basename(path))
  toss_winner <- scalar_or_na(info$toss$winner)
  toss_decision <- scalar_or_na(info$toss$decision)
  date <- scalar_or_na(info$dates)
  venue <- scalar_or_na(info$venue)
  city <- scalar_or_na(info$city)

  # The first two innings are the regulation innings. Extra innings in tied
  # matches are Super Overs and would leak the final result.
  primary_innings <- head(match$innings, 2)
  innings_rows <- lapply(seq_along(primary_innings), function(innings_number) {
    innings <- primary_innings[[innings_number]]
    batting_team <- scalar_or_na(innings$team)
    pp_overs <- Filter(function(over) as.integer(over$over) < 6L, innings$overs)
    deliveries <- unlist(lapply(pp_overs, function(over) over$deliveries), recursive = FALSE)
    runs <- sum(vapply(deliveries, function(delivery) {
      as.numeric(delivery$runs$total)
    }, numeric(1)))
    legal_balls <- count_legal_balls(deliveries)
    wickets <- count_wickets(deliveries)

    data.frame(
      match_id = match_id,
      date = date,
      season = season,
      venue = venue,
      city = city,
      team = batting_team,
      opponent = setdiff(teams, batting_team)[1],
      innings = innings_number,
      batting_first = as.integer(innings_number == 1),
      toss_winner = toss_winner,
      toss_decision = toss_decision,
      winner = winner,
      loser = loser,
      powerplay_runs = runs,
      powerplay_wickets = wickets,
      powerplay_legal_balls = legal_balls,
      powerplay_run_rate = ifelse(legal_balls > 0, runs / legal_balls * 6, NA_real_),
      stringsAsFactors = FALSE
    )
  })
  bind_rows(innings_rows)
}

json_files <- sort(list.files(data_dir, pattern = "[.]json$", full.names = TRUE))
if (length(json_files) == 0) stop("No JSON files found in ", data_dir)

message("Reading ", length(json_files), " Cricsheet match files...")
analysis_data <- bind_rows(lapply(json_files, parse_match)) %>%
  mutate(
    across(c(team, opponent, toss_winner, winner, loser), standardize_team),
    toss_win = as.integer(team == toss_winner),
    match_win = as.integer(team == winner),
    toss_decision_field = as.integer(toss_decision == "field"),
    score_band = cut(
      powerplay_runs,
      breaks = c(-Inf, 39, 49, 59, Inf),
      labels = c("Under 40", "40-49", "50-59", "60+"),
      ordered_result = TRUE
    ),
    wicket_band = cut(
      powerplay_wickets,
      breaks = c(-Inf, 0, 1, 2, Inf),
      labels = c("0", "1", "2", "3+"),
      ordered_result = TRUE
    )
  ) %>%
  arrange(date, match_id, innings)

# Keep only complete, internally consistent two-team matches.
match_quality <- analysis_data %>%
  group_by(match_id) %>%
  summarise(
    rows = n(),
    teams = n_distinct(team),
    wins = sum(match_win),
    toss_wins = sum(toss_win),
    full_powerplays = all(powerplay_legal_balls == 36),
    .groups = "drop"
  )
valid_ids <- match_quality %>%
  filter(rows == 2, teams == 2, wins == 1, toss_wins == 1, full_powerplays) %>%
  pull(match_id)
analysis_data <- analysis_data %>% filter(match_id %in% valid_ids)

quality_checks <- data.frame(
  check = c(
    "Raw JSON files", "Excluded without a binary winner", "Excluded without two complete powerplays",
    "Valid matches", "Analysis rows", "Duplicate match-team rows",
    "Missing key values", "Impossible run values", "Impossible wicket values"
  ),
  value = c(
    length(json_files),
    length(json_files) - nrow(match_quality),
    sum(!match_quality$full_powerplays),
    n_distinct(analysis_data$match_id), nrow(analysis_data),
    sum(duplicated(analysis_data[c("match_id", "team")])),
    sum(!complete.cases(analysis_data[c("match_id", "team", "winner", "powerplay_runs", "powerplay_wickets")])),
    sum(analysis_data$powerplay_runs < 0),
    sum(analysis_data$powerplay_wickets < 0 | analysis_data$powerplay_wickets > 10)
  )
)

write.csv(
  analysis_data,
  file.path(data_output_dir, "ipl_powerplay_match_level.csv"),
  row.names = FALSE,
  na = ""
)
write.csv(quality_checks, file.path(table_output_dir, "data_quality_checks.csv"), row.names = FALSE)

skewness <- function(x) mean((x - mean(x))^3) / stats::sd(x)^3
kurtosis <- function(x) mean((x - mean(x))^4) / stats::sd(x)^4
descriptive_statistics <- data.frame(
  variable = "powerplay_runs",
  n = sum(!is.na(analysis_data$powerplay_runs)),
  mean = mean(analysis_data$powerplay_runs),
  median = median(analysis_data$powerplay_runs),
  standard_deviation = sd(analysis_data$powerplay_runs),
  variance = var(analysis_data$powerplay_runs),
  skewness = skewness(analysis_data$powerplay_runs),
  kurtosis = kurtosis(analysis_data$powerplay_runs)
)
write.csv(descriptive_statistics, file.path(table_output_dir, "descriptive_statistics.csv"), row.names = FALSE)

probability_summary <- analysis_data %>%
  summarise(
    matches = n_distinct(match_id),
    p_win_given_toss_win = mean(match_win[toss_win == 1]),
    p_win_given_toss_loss = mean(match_win[toss_win == 0]),
    high_score_threshold = 50,
    p_win_given_high_powerplay_score = mean(match_win[powerplay_runs >= 50]),
    n_high_powerplay_score = sum(powerplay_runs >= 50)
  )
write.csv(probability_summary, file.path(table_output_dir, "conditional_probabilities.csv"), row.names = FALSE)

toss_winner_rows <- analysis_data %>% filter(toss_win == 1)
toss_ci <- binom.test(sum(toss_winner_rows$match_win), nrow(toss_winner_rows), conf.level = 0.95)

toss_table <- table(analysis_data$toss_win, analysis_data$match_win)
chi_test <- suppressWarnings(chisq.test(toss_table, correct = FALSE))
run_test <- t.test(
  powerplay_runs ~ match_win,
  data = analysis_data,
  alternative = "less",
  var.equal = FALSE
)

wicket_counts <- table(factor(analysis_data$powerplay_wickets, levels = 0:10))
lambda <- mean(analysis_data$powerplay_wickets)
n_wickets <- nrow(analysis_data)
observed_gof <- c(
  as.numeric(wicket_counts[1]),
  as.numeric(wicket_counts[2]),
  as.numeric(wicket_counts[3]),
  sum(as.numeric(wicket_counts[4:11]))
)
expected_gof <- n_wickets * c(
  dpois(0, lambda), dpois(1, lambda), dpois(2, lambda), ppois(2, lambda, lower.tail = FALSE)
)
poisson_statistic <- sum((observed_gof - expected_gof)^2 / expected_gof)
poisson_df <- length(observed_gof) - 2 # total constraint and estimated lambda
poisson_p <- pchisq(poisson_statistic, df = poisson_df, lower.tail = FALSE)

decision <- function(p) ifelse(p < 0.05, "Reject H0", "Fail to reject H0")
test_results <- bind_rows(
  data.frame(
    test = "Toss/result chi-square test",
    sample_size = nrow(analysis_data),
    null_hypothesis = "Toss result and match result are independent",
    alternative_hypothesis = "Toss result and match result are associated",
    alpha = 0.05,
    statistic = unname(chi_test$statistic),
    degrees_of_freedom = unname(chi_test$parameter),
    p_value = chi_test$p.value,
    decision = decision(chi_test$p.value),
    interpretation = ifelse(
      chi_test$p.value < 0.05,
      "Toss outcome is statistically associated with match outcome.",
      "The data do not show a statistically significant toss advantage."
    )
  ),
  data.frame(
    test = "Welch one-sided t-test: powerplay runs",
    sample_size = nrow(analysis_data),
    null_hypothesis = "Winners do not score more powerplay runs on average than losers",
    alternative_hypothesis = "Winners score more powerplay runs on average than losers",
    alpha = 0.05,
    statistic = -unname(run_test$statistic),
    degrees_of_freedom = unname(run_test$parameter),
    p_value = run_test$p.value,
    decision = decision(run_test$p.value),
    interpretation = ifelse(
      run_test$p.value < 0.05,
      "Winning teams have a statistically higher mean powerplay score.",
      "The data do not establish a higher mean powerplay score for winners."
    )
  ),
  data.frame(
    test = "Poisson goodness-of-fit: powerplay wickets",
    sample_size = n_wickets,
    null_hypothesis = "Powerplay wickets follow a Poisson distribution",
    alternative_hypothesis = "Powerplay wickets do not follow a Poisson distribution",
    alpha = 0.05,
    statistic = poisson_statistic,
    degrees_of_freedom = poisson_df,
    p_value = poisson_p,
    decision = decision(poisson_p),
    interpretation = ifelse(
      poisson_p < 0.05,
      "Powerplay wicket counts differ significantly from a fitted Poisson model.",
      "A fitted Poisson model is a plausible approximation for powerplay wickets."
    )
  )
)
write.csv(test_results, file.path(table_output_dir, "hypothesis_tests.csv"), row.names = FALSE)

confidence_intervals <- data.frame(
  estimate = unname(toss_ci$estimate),
  lower_95 = toss_ci$conf.int[1],
  upper_95 = toss_ci$conf.int[2],
  successes = sum(toss_winner_rows$match_win),
  sample_size = nrow(toss_winner_rows),
  method = "Exact binomial confidence interval"
)
write.csv(confidence_intervals, file.path(table_output_dir, "toss_win_probability_ci.csv"), row.names = FALSE)

logistic_model <- glm(
  match_win ~ toss_win + toss_decision_field + batting_first +
    powerplay_runs + powerplay_wickets,
  family = binomial(),
  data = analysis_data
)
model_matrix <- summary(logistic_model)$coefficients
logistic_results <- data.frame(
  term = rownames(model_matrix),
  estimate = model_matrix[, "Estimate"],
  standard_error = model_matrix[, "Std. Error"],
  z_statistic = model_matrix[, "z value"],
  p_value = model_matrix[, "Pr(>|z|)"],
  odds_ratio = exp(model_matrix[, "Estimate"]),
  conf_low = exp(model_matrix[, "Estimate"] - 1.96 * model_matrix[, "Std. Error"]),
  conf_high = exp(model_matrix[, "Estimate"] + 1.96 * model_matrix[, "Std. Error"]),
  row.names = NULL
)
write.csv(logistic_results, file.path(table_output_dir, "logistic_regression_odds_ratios.csv"), row.names = FALSE)

band_probabilities <- analysis_data %>%
  group_by(score_band, wicket_band, .drop = FALSE) %>%
  summarise(n = n(), win_probability = mean(match_win), .groups = "drop")
write.csv(band_probabilities, file.path(table_output_dir, "score_wicket_band_probabilities.csv"), row.names = FALSE)

theme_set(theme_minimal(base_size = 12))
save_plot <- function(filename, plot, width = 9, height = 6) {
  ggsave(file.path(figure_output_dir, filename), plot, width = width, height = height, dpi = 180)
}

toss_rates <- analysis_data %>%
  group_by(toss_status = ifelse(toss_win == 1, "Won toss", "Lost toss")) %>%
  summarise(wins = sum(match_win), n = n(), win_rate = mean(match_win), .groups = "drop") %>%
  rowwise() %>%
  mutate(
    ci = list(binom.test(wins, n)$conf.int),
    lower = ci[[1]][1], upper = ci[[1]][2]
  ) %>%
  ungroup()
p1 <- ggplot(toss_rates, aes(toss_status, win_rate, fill = toss_status)) +
  geom_col(width = 0.65, show.legend = FALSE) +
  geom_errorbar(aes(ymin = lower, ymax = upper), width = 0.15) +
  scale_y_continuous(labels = percent, limits = c(0, max(toss_rates$upper) + 0.08)) +
  labs(title = "IPL win rate after winning or losing the toss", x = NULL, y = "Match win rate", caption = "Error bars are exact 95% binomial confidence intervals.")
save_plot("01_toss_win_rate_ci.png", p1)

toss_decisions <- toss_winner_rows %>%
  count(toss_decision, result = ifelse(match_win == 1, "Won match", "Lost match")) %>%
  group_by(toss_decision) %>% mutate(proportion = n / sum(n)) %>% ungroup()
p2 <- ggplot(toss_decisions, aes(toss_decision, proportion, fill = result)) +
  geom_col(position = "dodge") +
  scale_y_continuous(labels = percent) +
  labs(title = "Match outcomes by decision made after winning the toss", x = "Toss decision", y = "Share of toss winners", fill = "Match result")
save_plot("02_toss_decision_result.png", p2)

p3 <- ggplot(analysis_data, aes(factor(match_win, labels = c("Lost", "Won")), powerplay_runs, fill = factor(match_win))) +
  geom_violin(alpha = 0.45, trim = FALSE, show.legend = FALSE) +
  geom_boxplot(width = 0.18, outlier.alpha = 0.18, show.legend = FALSE) +
  labs(title = "Powerplay scores of match winners and losers", x = "Match result", y = "Powerplay runs")
save_plot("03_powerplay_runs_by_result.png", p3)

p4 <- ggplot(band_probabilities, aes(wicket_band, score_band, fill = win_probability)) +
  geom_tile(color = "white", linewidth = 0.8) +
  geom_text(aes(label = ifelse(n == 0, "No data", paste0(percent(win_probability, accuracy = 1), "\n(n=", n, ")"))), size = 3.5) +
  scale_fill_gradient(low = "#f1eef6", high = "#045a8d", labels = percent, na.value = "grey90") +
  labs(title = "Win probability by powerplay score and wickets lost", x = "Powerplay wickets lost", y = "Powerplay score", fill = "Win probability")
save_plot("04_score_wicket_heatmap.png", p4)

max_wickets <- max(analysis_data$powerplay_wickets)
poisson_chart <- data.frame(
  wickets = 0:max_wickets,
  observed = as.numeric(table(factor(analysis_data$powerplay_wickets, levels = 0:max_wickets))),
  expected = n_wickets * dpois(0:max_wickets, lambda)
)
poisson_long <- rbind(
  data.frame(wickets = poisson_chart$wickets, series = "Observed", count = poisson_chart$observed),
  data.frame(wickets = poisson_chart$wickets, series = "Poisson expected", count = poisson_chart$expected)
)
p5 <- ggplot(poisson_long, aes(factor(wickets), count, fill = series)) +
  geom_col(position = "dodge") +
  labs(title = "Observed versus fitted Poisson powerplay wickets", subtitle = paste("Estimated lambda =", round(lambda, 2)), x = "Powerplay wickets", y = "Team-innings", fill = NULL)
save_plot("05_poisson_wickets.png", p5)

team_season <- analysis_data %>%
  group_by(team, season) %>%
  summarise(powerplay_run_rate = mean(powerplay_run_rate), win_rate = mean(match_win), matches = n(), .groups = "drop") %>%
  filter(matches >= 5)
team_season_long <- rbind(
  data.frame(team_season[c("team", "season", "matches")], metric = "Powerplay run rate", value = team_season$powerplay_run_rate),
  data.frame(team_season[c("team", "season", "matches")], metric = "Win rate (%)", value = 100 * team_season$win_rate)
)
p6 <- ggplot(team_season_long, aes(season, value, color = team, group = team)) +
  geom_line(alpha = 0.75, linewidth = 0.6) +
  geom_point(size = 1) +
  facet_wrap(~metric, scales = "free_y", ncol = 1) +
  labs(title = "Team-season powerplay run rate and win rate", subtitle = "Shown for team-seasons with at least five matches", x = "Season", y = NULL, color = "Team") +
  theme(legend.position = "right")
save_plot("06_team_season_trends.png", p6, width = 11, height = 8)

coefficient_plot <- logistic_results %>%
  filter(term != "(Intercept)") %>%
  mutate(term = recode(
    term,
    toss_win = "Won toss",
    toss_decision_field = "Toss decision: field",
    batting_first = "Batted first",
    powerplay_runs = "Powerplay runs (per run)",
    powerplay_wickets = "Powerplay wickets (per wicket)"
  ))
p7 <- ggplot(coefficient_plot, aes(odds_ratio, reorder(term, odds_ratio))) +
  geom_vline(xintercept = 1, linetype = "dashed", color = "grey45") +
  geom_errorbar(aes(xmin = conf_low, xmax = conf_high), width = 0.18, orientation = "y") +
  geom_point(size = 2.6, color = "#045a8d") +
  scale_x_log10() +
  labs(title = "Early-match predictors of winning", subtitle = "Logistic-regression odds ratios with 95% confidence intervals", x = "Odds ratio (log scale)", y = NULL)
save_plot("07_logistic_odds_ratios.png", p7)

message(
  "Analysis complete: ", n_distinct(analysis_data$match_id), " matches and ",
  nrow(analysis_data), " team-match rows written to ", output_dir, "."
)
