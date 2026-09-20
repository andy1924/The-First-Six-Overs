# IPL: Do the First Six Overs Matter?

## Project in one sentence

This project checks whether winning the toss and a team's score and wickets in
the first six overs are related to winning an IPL match.

## Run it

There is only one command to run:

```sh
Rscript R/01_analysis.R
```

It reads the JSON files in `dataset/` and creates the cleaned dataset, result
tables, and charts inside `output/`. The raw dataset is never changed.

The final written conclusion is in [analysis.md](analysis.md).

## Dataset used

- Source: [Cricsheet IPL ball-by-ball data](https://cricsheet.org/downloads/)
- Valid completed matches analysed: **1,227**
- Team-match rows analysed: **2,454**
- Excluded: 9 no-result matches and 7 matches without a complete six-over
  powerplay for both teams

## Final answer

The toss did **not** make a statistically significant difference to winning.
The first six overs did matter: winners scored more runs and, most importantly,
lost fewer wickets. A team scoring 50 or more runs in the powerplay won about
**59.7%** of the time.

| Question | Result |
| --- | --- |
| Does winning the toss improve winning probability? | No clear evidence (51.3% win rate; p = 0.183). |
| Do winners score more in the powerplay? | Yes: 51.4 runs versus 45.6 for losers (p < 0.001). |
| What is the strongest early signal? | Fewer powerplay wickets. Each extra wicket reduced estimated win odds by about 40%. |

## Results charts

### Toss result

Winning the toss and losing the toss led to very similar match win rates.

![Win rate after toss win or loss](output/figures/01_toss_win_rate_ci.png)

![Toss decision and match result](output/figures/02_toss_decision_result.png)

### Powerplay runs and wickets

Winners generally started with more runs. The best situation is a score of 60+
with no wicket lost; the most difficult is under 40 with three or more wickets
lost.

![Powerplay runs for winners and losers](output/figures/03_powerplay_runs_by_result.png)

![Win probability by score and wickets](output/figures/04_score_wicket_heatmap.png)

### Wickets and team trends

The wicket distribution is not a perfect Poisson distribution, and team starts
and conversion rates vary by season.

![Observed and expected powerplay wickets](output/figures/05_poisson_wickets.png)

![Team-season run rate and win rate](output/figures/06_team_season_trends.png)

### Which factors matter most?

The regression chart confirms that wickets lost and runs scored in the
powerplay are more useful early indicators than the toss.

![Logistic-regression odds ratios](output/figures/07_logistic_odds_ratios.png)

## Files to submit

- `R/01_analysis.R` — the single reproducible R script
- `output/data/ipl_powerplay_match_level.csv` — cleaned data
- `output/figures/` — final charts
- `analysis.md` — short final verdict
