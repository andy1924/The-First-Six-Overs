# IPL Mini Project Requirements

## Project title

**The First Six Overs and IPL Winning Probability**

## Aim and problem statement

In T20 cricket, commentators often claim that the first six overs create momentum and decide the match. This project tests that claim using real Indian Premier League ball-by-ball data. It estimates how toss outcome, toss decision, powerplay runs, and powerplay wickets are associated with the probability of winning an IPL match.

## Domain theory

The first six overs of an innings are the powerplay. Fielding restrictions can increase scoring opportunities, but attacking batters also face a greater risk of losing wickets. A team that wins the toss can choose to bat or field, and both decisions may affect strategy.

The match result is treated as a binary outcome: win or loss. The main explanatory variables are known by the end of the powerplay, so the project avoids using final-match information to predict the same match result.

## Dataset and reference

- **Dataset:** Cricsheet Indian Premier League ball-by-ball data
- **Website:** <https://cricsheet.org/downloads/>
- **Competition:** Indian Premier League
- **Preferred format:** JSON through the R `cricketdata` package
- **Data included:** Match result, toss winner, toss decision, innings, runs, wickets, teams, players, and ball-by-ball deliveries
- **Suggested citation:** Cricsheet. *Available match data downloads*. <https://cricsheet.org/downloads/>

## Research questions

| No. | Research question | Probability and Statistics concept |
|---|---|---|
| RQ1 | What is the probability of winning after winning the toss? | Conditional probability and Bayes theorem |
| RQ2 | Is toss result independent of match result? | Chi-square test of independence |
| RQ3 | Do winning teams score more in the powerplay than losing teams? | Mean, variance, confidence interval, t-test |
| RQ4 | Do powerplay wickets approximately follow a Poisson distribution? | Poisson distribution and goodness of fit |
| RQ5 | How does win probability change across powerplay score and wicket ranges? | Bivariate analysis and conditional probability |
| RQ6 | Which early-match variables are most associated with winning? | Correlation and logistic regression |

## Hypotheses

### Toss impact

- **H0:** Toss result and match result are independent.
- **H1:** Toss result and match result are associated.

### Powerplay score

- **H0:** Winning and losing teams have the same mean powerplay score.
- **H1:** Winning teams have a higher mean powerplay score.

### Powerplay wickets

- **H0:** Powerplay wickets follow a Poisson distribution with estimated lambda.
- **H1:** Observed wicket counts differ from the Poisson distribution.

## Data cleaning requirements

- Keep the original download unchanged.
- Remove abandoned and no-result matches.
- Standardize renamed or abbreviated team names across seasons.
- Keep only valid IPL matches with a winner and loser.
- Filter deliveries to the first six overs of each innings.
- Create `powerplay_runs`, `powerplay_wickets`, and `powerplay_run_rate` for every team-match.
- Create binary variables: `toss_win` and `match_win`.
- Check missing values, duplicate match IDs, and impossible scores or wicket values.
- Create score and wicket bands for conditional probability analysis.
- Save the final analysis table as `ipl_powerplay_match_level.csv`.

## Required R implementation

### Packages

| Package | Purpose |
|---|---|
| `cricketdata` | Download IPL match and ball-by-ball data from Cricsheet |
| `dplyr` | Cleaning, grouping, and aggregation |
| `tidyr` | Reshaping data |
| `ggplot2` | Visualisations |
| `broom` | Tidy hypothesis-test and regression output |
| `scales` | Percentage and axis formatting |

### Minimum import code

```r
install.packages(c("cricketdata", "dplyr", "tidyr", "ggplot2", "broom", "scales"))

library(cricketdata)
library(dplyr)
library(ggplot2)

ipl_balls <- fetch_cricsheet("bbb", "male", "ipl")
ipl_matches <- fetch_cricsheet("match", "male", "ipl")
```

## Required statistical analysis

| Analysis | Minimum output |
|---|---|
| Descriptive statistics | Mean, median, standard deviation, variance, skewness, and kurtosis of powerplay runs |
| Conditional probability | `P(match win \| toss win)` and `P(match win \| high powerplay score)` |
| Confidence interval | 95% confidence interval for match-win probability after winning the toss |
| Chi-square test | Test whether toss result and match result are independent |
| t-test | Compare mean powerplay runs for winning and losing teams |
| Poisson goodness-of-fit test | Compare observed and expected powerplay wicket counts |
| Logistic regression | Model match win using early-match variables and report odds ratios |

For every test, report the sample size, null hypothesis, alternative hypothesis, significance level, test statistic, p-value, decision, and cricket interpretation.

## Required visualisations

Create at least six charts. Each chart must have a descriptive title, labeled axes, readable legend where needed, and a short interpretation.

| Figure | Chart | Question answered |
|---|---|---|
| 1 | Bar chart with 95% CI: win rate after toss win versus toss loss | Does the toss improve winning probability? |
| 2 | Grouped bar chart: toss decision (bat or field) by match result | Does the post-toss decision matter? |
| 3 | Violin or box plot: powerplay runs for winners and losers | Do winners start with higher scores? |
| 4 | Heatmap: powerplay run band × wicket band → win probability | What is the best early-match situation? |
| 5 | Observed vs Poisson expected wicket-count chart | Is powerplay wicket loss approximately random? |
| 6 | Team-season line chart: powerplay run rate and win rate | Which teams convert fast starts into wins? |
| 7 | Regression coefficient plot with 95% CIs | Which early-match variables matter most? |

## Deliverables

- A report or presentation in this sequence:
  1. Project title
  2. Aim or problem statement
  3. Domain theory
  4. Data description with reference
  5. Data cleaning
  6. Data implementation
  7. Data analysis
  8. Conclusion
- A reproducible R script or R Markdown file.
- A cleaned match-level CSV.
- At least six final visualisations.
- A summary-statistics table.
- A conclusion answering the research questions.

## Scope and limitations

- This is an observational study, so association does not prove causation.
- Do not use final match totals as predictors of the result of that same match; that would leak the outcome.
- Use only information available by the end of the first six overs in the main win-probability analysis.
- Results apply to IPL matches and should not automatically be generalized to all cricket formats.

## Conclusion requirement

The conclusion should state whether toss, powerplay runs, and powerplay wickets were statistically associated with match outcomes; identify the strongest association; and explain why results may vary across seasons, teams, venues, and match contexts.
