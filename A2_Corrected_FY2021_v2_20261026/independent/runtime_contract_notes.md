# 已保存运行环境的独立合同核验

本程序只读取原始Rmd渲染后保存的runtime_environment.rds与共享CSV；未调用作者learn_recipe、fit或候选选择函数，未重跑模型、修改Rmd或重选超参数。
独立median用排序次序统计量求出；filled mean=sum(x)/n；sample sd=sqrt(sum((x-mean)^2)/(n-1))。仅在正确fitting rows上计算，并与runtime recipe逐参数比较。
已比较 138 个recipe参数，失败数 0；最大绝对差 2.220446049250313e-16（容差1e-12）。
逐项证据见runtime_contract_recipe_comparison.csv；final80% row IDs、labels、原numeric值见runtime_contract_training_identity.csv。

## Level A独立预测复现

从完整80% labels独立计算majority和class proportions，以seed5004调用base sample生成chance预测，与baseline的两个原始预测向量逐元素比较；不是只核对汇总metric。
      Run Predictor     N Prediction_Exact_Match Mismatched_Rows Seed  Majority
 baseline  majority 19201                   TRUE               0   NA Full-time
 baseline    chance 19201                   TRUE               0 5004 Full-time

## 各模型运行观察

- baseline: observed saved unchanged-Rmd environment
  - final refit N=76786; shared Train/Test IDs match=TRUE/TRUE; labels/raw numeric match=TRUE/TRUE
  - selected=reference only; forbidden predictors=
  - design: Training-majority / independent training-prior sample; no predictive design matrix
- logistic: observed saved unchanged-Rmd environment
  - final refit N=76786; shared Train/Test IDs match=TRUE/TRUE; labels/raw numeric match=TRUE/TRUE
  - selected=extended_linear; forbidden predictors=
  - design: Formula design: R factor contrasts, numeric z-scores/missing flags; selected quadratic age adds squared standardised Age
- lda: observed saved unchanged-Rmd environment
  - final refit N=76786; shared Train/Test IDs match=TRUE/TRUE; labels/raw numeric match=TRUE/TRUE
  - selected=extended_linear; forbidden predictors=
  - design: Explicit treatment contrasts, intercept removed; fitting-only within-class variance and QR rank filtering; classical pooled covariance
- tree: observed saved unchanged-Rmd environment
  - final refit N=76786; shared Train/Test IDs match=TRUE/TRUE; labels/raw numeric match=TRUE/TRUE
  - selected=extended_linear; forbidden predictors=
  - design: rpart factor-aware formula design; numeric z-scores/missing flags, no one-hot requirement
- knn: observed saved unchanged-Rmd environment
  - final refit N=76786; shared Train/Test IDs match=TRUE/TRUE; labels/raw numeric match=TRUE/TRUE
  - selected=extended_linear; forbidden predictors=
  - design: All-level categorical one-hot /sqrt(2); numeric z-scores; missingness 0/1 left unscaled
- svm: observed saved unchanged-Rmd environment
  - final refit N=76786; shared Train/Test IDs match=TRUE/TRUE; labels/raw numeric match=TRUE/TRUE
  - selected=extended; forbidden predictors=
  - design: All-level 0/1 one-hot, fitting-only constant-column filter; numeric z-scores, missingness 0/1; e1071 scale=FALSE

## 收敛与LDA数值解释

Logistic完整candidate convergence/value/最终convergence保存在runtime_contract_logistic_convergence.json及candidate CSV。返回码非0的分数可计算，但不能据渲染成功宣称充分优化。
已保存实际安装nnet::multinom与nnet.default实现；multinom多分类调用使用size=0、skip=TRUE、rang=0，初始weights为零。因此不能凭nnet通常随机初始化而编造本multinom拟合具有未设seed的随机start。
LDA final pooled within-class covariance、class means及scaling分别导出；诊断JSON含empirical/equal prior、candidate/final N、rank、eigenvalues、dropped列及有限性检查。共享covariance可逆和rank充分并不证明Gaussian或类间协方差相等。
SVM class weights按精确candidate/final labels独立计算N/(8*n_k)，与原class_weights()纯函数输出比较（none应返回NULL）；没有调用fit_svm。native model parameters JSON及support-vector index→original CSV映射只读取已保存final model；未存储的native class weights或probability flags保留null，不虚构。
全局R options不存于runtime environment；本次保存vanilla verifier的contrasts及Logistic fitted model中的实际contrasts，不冒称已恢复原render的全部global options。
后续kNN/SVM保存环境后重跑本脚本即可补全，不会重新执行任何Rmd。

