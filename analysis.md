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
| Toss decision, among toss winners | p = 0.005 | Fielding first won 54.2%; batting first won 45.7%. |
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

## Secondary finding: the toss decision

Winning the toss is not the same as using it well. Among the 1,227 toss winners
the decision they made divides them: the 816 who elected to field first won
**54.2%** of their matches (442 wins), while the 411 who elected to bat first won
**45.7%** (188 wins). That 8.5-point gap is significant on its own — 95%
confidence interval 2.6 to 14.4 points, chi-square = 7.77, p = 0.005.

This is a raw comparison, and it weakens under control. In the logistic
regression the field-first indicator sits at an odds ratio of about 1 once
powerplay runs and wickets are in the model, so the gap does not survive
adjustment. Teams that choose to bat may also differ systematically from teams
that choose to field — venue, dew, and squad strength all influence the decision
— so this is best read as a description of strategy rather than a proven edge.

## What this does not show

This does not prove that the powerplay causes the result. Stronger teams,
opposition, venue, season, and match conditions can affect both the start of an
innings and the final result.

## One-line verdict

**The toss is a small advantage at most; a strong, low-wicket powerplay is the
clearer sign of an IPL win.**
