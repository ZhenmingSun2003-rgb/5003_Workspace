args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(args[1], winslash = "/")
path <- file.path(root, "WVS_Wave7_cleaned_for_modelling.csv")
header <- names(read.csv(path, nrows = 0, check.names = FALSE))
classes <- rep("NULL", length(header)); classes[match("Q279", header)] <- "integer"
y <- read.csv(path, colClasses = classes, check.names = FALSE)$Q279
stopifnot(length(y) == 95987, all(y %in% 1:8))
# Independent reconstruction: sample each class in label order and sort original row numbers.
set.seed(5003)
pool <- integer()
for (cls in 1:8) {
  rows <- which(y == cls)
  pool <- c(pool, sample(rows, size = floor(0.8 * length(rows)), replace = FALSE))
}
pool <- sort(pool)
test <- which(!seq_along(y) %in% pool)
set.seed(5005)
local_train <- integer()
for (cls in 1:8) {
  rows <- which(y[pool] == cls)
  local_train <- c(local_train, sample(rows, size = floor(0.75 * length(rows)), replace = FALSE))
}
local_train <- sort(local_train)
local_val <- which(!seq_along(pool) %in% local_train)
partition <- rep("Test", length(y))
partition[pool[local_train]] <- "Train"
partition[pool[local_val]] <- "Validation"
labs <- c("Full-time", "Part-time", "Self-employed", "Retired", "Housewife", "Student", "Unemployed", "Other")
write.csv(data.frame(row_id = seq_along(y), target_code = y, truth = labs[y], partition = partition),
          file.path(root, "independent", "reference_split.csv"), row.names = FALSE)
write.csv(data.frame(local_dev_id = local_train), file.path(root, "independent", "reference_dev_id.csv"), row.names = FALSE)
write.csv(data.frame(local_val_id = local_val), file.path(root, "independent", "reference_val_id.csv"), row.names = FALSE)
for (cap in c(25000, 10000)) {
  set.seed(5006)
  sel <- integer()
  for (cls in 1:8) {
    rows <- which(y[pool[local_train]] == cls)
    sel <- c(sel, sample(rows, size = floor(length(rows) * cap / length(local_train)), replace = FALSE))
  }
  sel <- sort(sel)
  write.csv(data.frame(row_id = pool[local_train[sel]], local_dev_id = local_train[sel], fit_id = sel),
            file.path(root, "independent", paste0("reference_cap_", cap, ".csv")), row.names = FALSE)
}
writeLines(capture.output(sessionInfo()), file.path(root, "environment", "independent_R_session.txt"))
print(table(partition))
print(table(factor(y[test], levels = 1:8)))
