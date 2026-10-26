
input <- jsonlite::fromJSON(paste(readLines(file("stdin"),warn=FALSE),collapse="\n"),simplifyVector=FALSE)
extract <- function(path) {
  lines <- readLines(path,warn=FALSE,encoding="UTF-8"); active<-FALSE; code<-character()
  for(line in lines) {
    if(grepl("^\x60\x60\x60\\{r[ ,}]",line)){active<-TRUE;next}
    if(active && grepl("^\x60\x60\x60[[:space:]]*$",line)){active<-FALSE;next}
    if(active)code<-c(code,line)
  }
  expressions <- parse(text=code,keep.source=FALSE); found<-list()
  walk <- function(x) {
    if(missing(x))return(invisible(NULL))
    if(is.call(x) && identical(x[[1]],as.name("<-")) && is.symbol(x[[2]]) && as.character(x[[2]]) %in% c("core","extended","SPECIFICATIONS"))found[[length(found)+1L]]<<-x
    if(is.call(x)||is.expression(x)||is.pairlist(x))for(child in as.list(x))walk(child)
  }
  walk(expressions); e<-new.env(parent=baseenv())
  for(assignment in found) {
    rhs<-assignment[[3]]
    stopifnot(is.call(rhs),as.character(rhs[[1]]) %in% c("c","list"))
    eval(assignment,e)
  }
  stopifnot(exists("SPECIFICATIONS",e,inherits=FALSE),is.list(e$SPECIFICATIONS),length(e$SPECIFICATIONS)>0L)
  list(specifications=e$SPECIFICATIONS,constant_assignments_evaluated=vapply(found,function(x)as.character(x[[2]]),""),
       scope="Only constant c()/list() assignments defining core/extended/SPECIFICATIONS evaluated; no model/data/Test code")
}
results<-lapply(input$files,function(item)list(file=item$file,original=extract(item$old),corrected=extract(item$new)))
cat(jsonlite::toJSON(list(files=results),pretty=TRUE,auto_unbox=TRUE))
