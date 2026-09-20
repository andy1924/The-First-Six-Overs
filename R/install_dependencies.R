packages <- c(
  "cricketdata", "jsonlite", "dplyr", "tidyr", "ggplot2", "broom",
  "scales", "knitr", "rmarkdown"
)

missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing) > 0) {
  install.packages(missing, repos = "https://cloud.r-project.org")
} else {
  message("All project dependencies are already installed.")
}

