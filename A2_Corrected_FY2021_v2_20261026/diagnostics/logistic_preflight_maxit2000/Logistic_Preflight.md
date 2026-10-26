---
title: 'Logistic convergence preflight: Train and Validation only'
output:
  html_document:
    toc: true
---

Corrected 01 source SHA-256: `516d23f073cfff3ded7a107a9d6cbc6904e937cf33bd470bff4789be78364141`.

This diagnostic preserves the original six candidates, validation ranking and full-80% refit. It omits Test preprocessing, predictions and scores. MAXIT is assessed for convergence only; no Test metric is available to this diagnostic.



## Original corrected chunk: setup


``` r
SEED <- 5003
TRAIN_FRACTION <- 0.80
DEV_CAP <- 25000L
# Iteration-only correction: retain the original model/search, require convergence.
MAXIT <- 2000L
TARGET_LABELS <- c("Full-time", "Part-time", "Self-employed", "Retired",
                   "Housewife", "Student", "Unemployed", "Other")
REQUIRED_COLUMNS <- c("Q279", "B_COUNTRY_ALPHA", "Q260", "Q262", "Q270",
                      "Q273", "Q274", "Q275", "Q286", "Q287", "Q288")
if (!requireNamespace("nnet", quietly=TRUE)) stop("Install R's recommended package 'nnet'.")
resolve_dataset <- function(filename="WVS_Wave7_cleaned_for_modelling.csv") {
  candidates <- getwd()
  if (requireNamespace("knitr", quietly=TRUE)) {
    f <- tryCatch(knitr::current_input(dir=TRUE), error=function(e) "")
    if (length(f)==1L && nzchar(f))
      candidates <- c(candidates, dirname(normalizePath(f, mustWork=FALSE)))
  }
  candidates <- unique(c(candidates, dirname(candidates)))
  hits <- file.path(candidates, filename)
  hits <- hits[file.exists(hits)]
  if (!length(hits)) stop("CSV not beside Rmd / working directory. Run git lfs pull.")
  p <- normalizePath(hits[1], mustWork=TRUE)
  if (file.info(p)$size < 1000) stop("LFS pointer found. Run git lfs pull.")
  p
}
read_selected <- function(p, wanted) {
  cols <- names(read.csv(p, nrows=0, check.names=FALSE))
  if (!all(wanted %in% cols)) stop("Missing columns: ", paste(setdiff(wanted,cols),collapse=","))
  types <- rep("NULL", length(cols))
  types[match(wanted, cols)] <- NA_character_
  read.csv(p, colClasses=types, check.names=FALSE, stringsAsFactors=FALSE,
           na.strings=c("", "NA"))
}
stratified_indices <- function(y, frac, seed) {
  set.seed(seed)
  g <- split(seq_along(y), y, drop=TRUE)
  sort(unlist(lapply(g, function(ids) sample(ids, floor(length(ids)*frac))), use.names=FALSE))
}
wvs <- read_selected(resolve_dataset(), REQUIRED_COLUMNS)
stopifnot(nrow(wvs)>1000, all(as.character(wvs$Q279) %in% as.character(1:8)))
wvs$Outcome <- factor(as.character(wvs$Q279),levels=as.character(1:8),labels=TARGET_LABELS)
train_id <- stratified_indices(wvs$Outcome, TRAIN_FRACTION, SEED)
test_id <- setdiff(seq_len(nrow(wvs)), train_id)
train <- wvs[train_id,,drop=FALSE]
test <- wvs[test_id,,drop=FALSE]
stopifnot(!length(intersect(train_id,test_id)),all(table(train$Outcome)>0),
          all(table(test$Outcome)>0))
cat("Train:",nrow(train)," Test:",nrow(test),"\n")
```

```
## Train: 76786  Test: 19201
```

## Original corrected chunk: country-map


``` r
WB_GROUPS <- list(
  Low=c("ETH","TJK"),
  `Lower-middle`=c("BGD","BOL","EGY","IND","KEN","KGZ","MAR","MMR","MNG",
                   "NGA","NIC","PAK","PHL","TUN","UKR","UZB","VNM","ZWE"),
  `Upper-middle`=c("ARG","ARM","BRA","CHN","COL","ECU","GTM","IDN","IRN",
                   "IRQ","JOR","KAZ","LBN","LBY","MDV","MEX","MYS","PER",
                   "RUS","SRB","THA","TUR","VEN"),
  High=c("AND","AUS","CAN","CHL","CYP","CZE","DEU","GBR","GRC","HKG","JPN",
         "KOR","MAC","NIR","NLD","NZL","PRI","ROU","SGP","SVK","TWN","URY","USA"),
  Unclassified=character(0)
)
country_map <- setNames(rep(names(WB_GROUPS),lengths(WB_GROUPS)),
                        unlist(WB_GROUPS,use.names=FALSE))
stopifnot(!anyDuplicated(names(country_map)))
unknown_codes <- setdiff(unique(as.character(wvs$B_COUNTRY_ALPHA)),names(country_map))
if (length(unknown_codes)) stop("Unmapped countries: ",paste(unknown_codes,collapse=","))
train$Income_Group <- unname(country_map[as.character(train$B_COUNTRY_ALPHA)])
test$Income_Group <- unname(country_map[as.character(test$B_COUNTRY_ALPHA)])
```

## Original corrected chunk: preprocessing


``` r
NUMERIC_KEYS <- c(Age="Q262",HouseholdSize="Q270",Children="Q274")
CATEGORY_KEYS <- list(
  Gender=as.character(1:2),Marital=as.character(1:6),
  Education=as.character(0:8),SocialClass=as.character(1:5),
  IncomeBracket=as.character(1:10),Savings=as.character(1:4),
  Income_Group=c("Low","Lower-middle","Upper-middle","High","Unclassified"))
CATEGORY_SOURCES <- c(Gender="Q260",Marital="Q273",Education="Q275",
                      SocialClass="Q287",IncomeBracket="Q288",
                      Savings="Q286",Income_Group="Income_Group")
numeric_value <- function(v) {
  x <- suppressWarnings(as.numeric(as.character(v)))
  x[!is.finite(x)] <- NA_real_
  x
}
learn_recipe <- function(raw) {
  num <- lapply(NUMERIC_KEYS,function(k) numeric_value(raw[[k]]))
  med <- vapply(num,function(x) if(all(is.na(x))) 0 else median(x,na.rm=TRUE),0.0)
  filled <- Map(function(x,m) {x[is.na(x)] <- m;x},num,med)
  mu <- vapply(filled,mean,0.0)
  sigma <- vapply(filled,sd,0.0)
  sigma[is.na(sigma)|sigma==0] <- 1
  list(median=med,mean=mu,sd=sigma)
}
apply_recipe <- function(raw,r) {
  out <- data.frame(Outcome=factor(as.character(raw$Outcome),levels=TARGET_LABELS))
  for (nm in names(NUMERIC_KEYS)) {
    x <- numeric_value(raw[[NUMERIC_KEYS[[nm]]]])
    missing <- is.na(x)
    x[missing] <- r$median[[nm]]
    out[[nm]] <- (x-r$mean[[nm]])/r$sd[[nm]]
    out[[paste0(nm,"_missing")]] <- as.integer(missing)
  }
  out$Age_sq <- out$Age^2
  for(nm in names(CATEGORY_KEYS)) {
    v <- trimws(as.character(raw[[CATEGORY_SOURCES[[nm]]]]))
    v[is.na(v)|!(v %in% CATEGORY_KEYS[[nm]])] <- "Missing"
    out[[nm]] <- factor(v,levels=c(CATEGORY_KEYS[[nm]],"Missing"))
  }
  out
}
```

## Original corrected chunk: evaluation


``` r
evaluate_8class <- function(truth,pred,show_confusion=FALSE) {
  a <- factor(as.character(truth),levels=TARGET_LABELS)
  b <- factor(as.character(pred),levels=TARGET_LABELS)
  if(anyNA(a)||anyNA(b)) stop("Invalid target class")
  cm <- table(True=a,Predicted=b)
  tp <- diag(cm);support <- rowSums(cm);calls <- colSums(cm)
  precision <- ifelse(calls>0,tp/calls,0)
  recall <- ifelse(support>0,tp/support,0)
  f1 <- ifelse(precision+recall>0,2*precision*recall/(precision+recall),0)
  overall <- data.frame(Macro_F1=mean(f1),Weighted_F1=sum(support*f1)/sum(support),
                        Accuracy=sum(tp)/sum(cm))
  per_class <- data.frame(Class=TARGET_LABELS,Support=as.integer(support),
                          Precision=precision,Recall=recall,F1=f1)
  if(show_confusion) print(cm)
  list(overall=overall,per_class=per_class,confusion=cm)
}
SPECIFICATIONS <- list(
 core_linear=c("Age","Age_missing","Gender","Marital","Education","SocialClass",
               "IncomeBracket"),
 extended_linear=c("Age","Age_missing","HouseholdSize","HouseholdSize_missing",
                   "Children","Children_missing","Gender","Marital","Education",
                   "SocialClass","IncomeBracket","Savings","Income_Group"),
 extended_quadratic_age=c("Age","Age_missing","Age_sq","HouseholdSize",
                           "HouseholdSize_missing","Children","Children_missing",
                           "Gender","Marital","Education","SocialClass",
                           "IncomeBracket","Savings","Income_Group"))
model_formula <- function(name) reformulate(SPECIFICATIONS[[name]],response="Outcome")
```

## Original corrected chunk: validation


``` r
dev_id <- stratified_indices(train$Outcome,0.75,SEED + 2)
val_id <- setdiff(seq_len(nrow(train)),dev_id)
cat("Seed:", SEED, "| initial Train:", length(dev_id),
    "| Validation:", length(val_id), "| Test:", nrow(test),
    "| Final refit pool:", nrow(train), "\n")
```

```
## Seed: 5003 | initial Train: 57587 | Validation: 19199 | Test: 19201 | Final refit pool: 76786
```

``` r
if(length(dev_id)>DEV_CAP) {
  short <- stratified_indices(train$Outcome[dev_id],DEV_CAP/length(dev_id),SEED + 3)
  dev_id <- dev_id[short]
}
development <- train[dev_id,,drop=FALSE]
validation <- train[val_id,,drop=FALSE]
r_dev <- learn_recipe(development)
x_dev <- apply_recipe(development,r_dev)
x_val <- apply_recipe(validation,r_dev)
grid <- expand.grid(Spec=names(SPECIFICATIONS),Decay=c(0.001,0.01),
                    stringsAsFactors=FALSE)
result_rows <- vector("list",nrow(grid))
for(i in seq_len(nrow(grid))) {
  spec <- grid$Spec[[i]];decay <- grid$Decay[[i]]
  fit <- nnet::multinom(model_formula(spec),data=x_dev,decay=decay,
                       maxit=MAXIT,MaxNWts=10000,trace=FALSE)
  if(!identical(as.integer(fit$convergence),0L))
    stop("Candidate did not converge; selection blocked: ",spec," decay=",decay,
         "; convergence=",fit$convergence,"; MAXIT=",MAXIT)
  pred <- predict(fit,newdata=x_val,type="class")
  met <- evaluate_8class(x_val$Outcome,pred)$overall
  result_rows[[i]] <- data.frame(Spec=spec,Decay=decay,Dev_N=nrow(x_dev),
                                 Val_N=nrow(x_val),Convergence=fit$convergence,
                                 Macro_F1=met$Macro_F1,Weighted_F1=met$Weighted_F1,
                                 Accuracy=met$Accuracy)
}
ranking <- do.call(rbind,result_rows)
stopifnot(nrow(ranking)==nrow(grid),all(ranking$Convergence==0L))
ranking <- ranking[order(-ranking$Macro_F1,-ranking$Weighted_F1,
                         match(ranking$Spec,names(SPECIFICATIONS)),-ranking$Decay),]
knitr::kable(ranking,digits=4,caption="Train-only validation ranking")
```



Table: Train-only validation ranking

|   |Spec                   | Decay| Dev_N| Val_N| Convergence| Macro_F1| Weighted_F1| Accuracy|
|:--|:----------------------|-----:|-----:|-----:|-----------:|--------:|-----------:|--------:|
|5  |extended_linear        | 0.010| 24996| 19199|           0|   0.3534|      0.4731|   0.5302|
|2  |extended_linear        | 0.001| 24996| 19199|           0|   0.3533|      0.4731|   0.5302|
|6  |extended_quadratic_age | 0.010| 24996| 19199|           0|   0.3523|      0.4725|   0.5323|
|3  |extended_quadratic_age | 0.001| 24996| 19199|           0|   0.3522|      0.4724|   0.5322|
|1  |core_linear            | 0.001| 24996| 19199|           0|   0.3371|      0.4515|   0.5163|
|4  |core_linear            | 0.010| 24996| 19199|           0|   0.3370|      0.4515|   0.5163|

``` r
winning_spec <- ranking$Spec[[1]]
winning_decay <- ranking$Decay[[1]]
cat("Chosen before final test:",winning_spec," decay=",winning_decay,"\n")
```

```
## Chosen before final test: extended_linear  decay= 0.01
```

## Final full-80% refit without Test prediction


``` r
preflight_final_start <- proc.time()[['elapsed']]
recipe_final <- learn_recipe(train)
X_train <- apply_recipe(train,recipe_final)
final_fit <- nnet::multinom(model_formula(winning_spec),data=X_train,
                           decay=winning_decay,maxit=MAXIT,MaxNWts=10000,trace=FALSE)
if(!identical(as.integer(final_fit$convergence),0L))
  stop("Final optimisation did not converge; Test scoring blocked. convergence=",
       final_fit$convergence,"; MAXIT=",MAXIT)
preflight_final_elapsed <- proc.time()[['elapsed']] - preflight_final_start
stopifnot(all(ranking$Convergence==0L), identical(as.integer(final_fit$convergence),0L),
          nrow(X_train)==76786L, !exists('X_test',inherits=FALSE),
          !exists('predicted',inherits=FALSE), !exists('majority_met',inherits=FALSE),
          !exists('comparison',inherits=FALSE))
cat('Candidate convergence codes:',ranking$Convergence,'\n')
```

```
## Candidate convergence codes: 0 0 0 0 0 0
```

``` r
cat('Final convergence:',final_fit$convergence,'objective:',format(final_fit$value,digits=16),'\n')
```

```
## Final convergence: 0 objective: 101183.8231029495
```

``` r
cat('Final full-80% block seconds:',preflight_final_elapsed,'\n')
```

```
## Final full-80% block seconds: 82.58
```

No Test prediction or Test performance is produced by this preflight.

