# Final Verdict: The First Six Overs and IPL Winning Probability

## Aim

To find whether the toss and first-six-over performance are related to winning
an IPL match.

## Data

The analysis used 1,227 completed IPL matches from Cricsheet. Each match gives
two observations: one for each team. No-result matches and matches where both
teams did not complete six overs were excluded.

## What we found

| Finding | Result | Simple meaning |
| --- | ---: | --- |
| Win rate after winning toss | 51.3% | Almost the same as a 50-50 chance. |
| Toss chi-square test | p = 0.183 | The toss was not significantly related to winning. |
| Mean powerplay runs: winners | 51.4 | Winners started faster. |
| Mean powerplay runs: losers | 45.6 | Losers scored about 5.8 fewer runs. |
| Powerplay-runs t-test | p < 0.001 | The difference in starts is statistically significant. |
| Win rate after 50+ powerplay runs | 59.7% | A fast start improves the chance of winning. |
| Effect of one extra powerplay wicket | odds ratio = 0.60 | One extra wicket reduced estimated win odds by about 40%. |

## Final conclusion

Winning the toss alone did not decide IPL matches in this dataset. The first
six overs were more important: teams that scored more runs and protected their
wickets were more likely to win. The strongest early indicator was **not
losing wickets in the powerplay**.

This does not prove that the powerplay causes the result. Stronger teams,
opposition, venue, season, and match conditions can affect both the start of an
innings and the final result.

## One-line verdict

**The toss is a small advantage at most; a strong, low-wicket powerplay is the
clearer sign of an IPL win.**
