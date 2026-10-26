args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(args[1],winslash="/",mustWork=TRUE)
.libPaths(c("C:/Users/Saberken/Documents/ChatGPT/5003_A1_A2/audit_20261024_01/r_library","C:/Users/Saberken/AppData/Local/R/win-library/4.6",.libPaths()))
a <- readRDS(file.path(root,"diagnostics/logistic_preflight_maxit2000/preflight_environment.rds"))
b <- readRDS(file.path(root,"results/logistic/runtime_environment.rds"))
result <- list(Purpose="Training-only preflight versus official fit; no predictions or metric evaluation called",
  Selected_Specification_Equal=identical(a$winning_spec,b$winning_spec),
  Selected_Decay_Equal=identical(a$winning_decay,b$winning_decay),
  All_Validation_Ranking_Values_Equal=isTRUE(all.equal(a$ranking,b$ranking,tolerance=1e-14)),
  Fitting_Train_IDs_Equal=identical(a$train_id,b$train_id),
  Candidate_Fit_IDs_Equal=identical(a$dev_id,b$dev_id),
  Validation_IDs_Equal=identical(a$val_id,b$val_id),
  Preflight_Final_Convergence=a$final_fit$convergence,Official_Final_Convergence=b$final_fit$convergence,
  Preflight_Objective=a$final_fit$value,Official_Objective=b$final_fit$value,
  Final_Objective_Absolute_Difference=abs(a$final_fit$value-b$final_fit$value),
  Final_Weights_Exactly_Equal=identical(a$final_fit$wts,b$final_fit$wts),
  Final_Weights_Maximum_Absolute_Difference=max(abs(a$final_fit$wts-b$final_fit$wts)),
  Preflight_Contains_Test_Predictions=exists("predicted",a,inherits=FALSE),
  Official_Test_Predictions_N=length(b$predicted))
stopifnot(result$Selected_Specification_Equal,result$Selected_Decay_Equal,result$All_Validation_Ranking_Values_Equal,
  result$Fitting_Train_IDs_Equal,result$Candidate_Fit_IDs_Equal,result$Validation_IDs_Equal,
  result$Preflight_Final_Convergence==0,result$Official_Final_Convergence==0,
  result$Final_Objective_Absolute_Difference<1e-8,result$Final_Weights_Maximum_Absolute_Difference<1e-10,
  !result$Preflight_Contains_Test_Predictions,result$Official_Test_Predictions_N==19201)
jsonlite::write_json(result,file.path(root,"diagnostics/logistic_training_replay_comparison.json"),pretty=TRUE,auto_unbox=TRUE,null="null",digits=16)
print(result)
