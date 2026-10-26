args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(args[1], winslash="/", mustWork=TRUE)
json <- jsonlite::fromJSON(file.path(root,"FY2021_crosswalk.json"))
canonical <- setNames(json$entries$group, json$entries$code)
files <- c("baseline.Rmd","02_LDA.Rmd","03_kNN.Rmd","04_SVM.Rmd","05_DecisionTree.Rmd")
r_code <- function(path) {
  lines <- readLines(path,warn=FALSE,encoding="UTF-8"); active <- FALSE; code <- character()
  for (line in lines) {
    if (grepl("^\x60\x60\x60\\{r[ ,}]",line)) {active<-TRUE;next}
    if(active && grepl("^\x60\x60\x60[[:space:]]*$",line)) {active<-FALSE;next}
    if(active) code<-c(code,line)
  }
  parse(text=code,keep.source=FALSE)
}
function_bodies <- function(expressions) {
  found <- list()
  walk <- function(x) {
    if (missing(x)) return(invisible(NULL))
    if (is.call(x) && identical(x[[1]],as.name("function"))) found[[length(found)+1L]] <<- x
    if (is.call(x) || is.expression(x) || is.pairlist(x)) for (child in as.list(x)) walk(child)
  }
  walk(expressions); found
}
protected <- c("SEED","TRAIN_FRACTION","TARGET_LEVELS","TARGET_LABELS","REQUIRED_COLUMNS","NUMERIC_KEYS","CATEGORY_KEYS","CATEGORY_SOURCES","SPECIFICATIONS","DEV_CAP","MAXIT","K_GRID","WEIGHTINGS","GRID","grid")
protected_assignments <- function(expressions) {
  found <- list()
  walk <- function(x) {
    if (missing(x)) return(invisible(NULL))
    if (is.call(x) && identical(x[[1]],as.name("<-")) && is.symbol(x[[2]]) && as.character(x[[2]]) %in% protected)
      found[[length(found)+1L]] <<- x
    if (is.call(x) || is.expression(x) || is.pairlist(x)) for (child in as.list(x)) walk(child)
  }
  walk(expressions); found
}
results <- lapply(files,function(filename) {
  old <- r_code(file.path(root,"original_sources",filename)); new <- r_code(file.path(root,filename))
  ma <- list()
  collect_map <- function(x) {
    if (missing(x)) return(invisible(NULL))
    if (is.call(x) && identical(x[[1]],as.name("<-")) && identical(x[[2]],as.name("WB_GROUPS"))) ma[[length(ma)+1L]] <<- x
    if (is.call(x) || is.expression(x) || is.pairlist(x)) for (child in as.list(x)) collect_map(child)
  }
  collect_map(new)
  stopifnot(length(ma)==1L)
  e <- new.env(parent=baseenv()); eval(ma[[1]],e)
  groups <- e$WB_GROUPS
  actual <- setNames(rep(names(groups),lengths(groups)),unlist(groups,use.names=FALSE))
  stopifnot(!anyDuplicated(names(actual)),identical(actual[sort(names(actual))],canonical[sort(names(canonical))]),
            identical(groups$Unclassified,character(0)),
            identical(function_bodies(old),function_bodies(new)),
            identical(protected_assignments(old),protected_assignments(new)))
  list(file=filename,R_chunks_parse=TRUE,canonical_66_map_equal=TRUE,unused_Unclassified_character0=TRUE,
       all_function_bodies_identical=TRUE,protected_contract_assignments_identical=TRUE,
       function_count=length(function_bodies(new)),protected_assignment_count=length(protected_assignments(new)))
})
jsonlite::write_json(list(status="PASS",scope="Parse/evaluate mapping only; no model fitting or dataset processing",files=results),
                    file.path(root,"environment","mapping_R_independent_check.json"),pretty=TRUE,auto_unbox=TRUE)
cat("PARSE_AND_INDEPENDENT_R_MAP_FUNCTION_CONTRACT_CHECK: PASS for all five corrected root Rmds\n")
