# IPL Powerplay Winning Probability

This project tests whether the toss and the first six overs are associated with
winning an IPL match. It uses the Cricsheet JSON files already stored in
`dataset/` and produces a two-row-per-match analysis table (one row for each
team), statistical results, and seven figures.

## Run the analysis

From the project root:

```sh
Rscript R/01_analysis.R
```

The script creates:

- `output/data/ipl_powerplay_match_level.csv`
- `output/tables/*.csv`
- `output/figures/*.png`

To render the report after the analysis has run:

```sh
Rscript -e 'rmarkdown::render("report.Rmd", output_dir = "output/report")'
```

Install any missing dependencies with:

```sh
Rscript R/install_dependencies.R
```

The raw files in `dataset/` are read-only inputs and are never modified.

