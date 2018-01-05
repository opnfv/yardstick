# ----------------------------------------------------------------------
# title: TOM useful functions
# author: Alassane Samba (alassane.samba@orange.com)
# Copyright (c) 2017 Orange
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ----------------------------------------------------------------------
############
### Evaluate a prediction
############
prediction_evaluator_with_p<-function(pred, actual, p){
  ##error
  error=actual-pred
  ## null ndeviance
  null.deviance=sum((mean(actual)-actual)^2)
  ## deviance : sum of squared error
  se=sum(error^2)
  ## n
  n=length(actual)
  ## mean squared error
  mse=se/n
  ## root mean squared error
  rmse=sqrt(mse)
  ## normalized root mean squared error
  nrmse=sqrt(mse/(null.deviance/n))
  ## r2 : coef of determination
  r2=1-(se/null.deviance)
  #adjusted r2
  adfR2=1-(1-r2)*((n-1)/(n-p))
  ## absolute error ratio
  abs.error.ratio=abs(error/actual)
  ## mean absolute error ratio
  mean.abs.error.ratio=mean(abs.error.ratio)
  ## median absolute error ratio
  med.abs.error.ratio=median(abs.error.ratio)
  ## 80th-percentile absolute error ratio
  perc80.abs.error.ratio=quantile(abs.error.ratio,0.8)
  ## return :
  return(list(p=p,n=n,sd=sqrt(null.deviance/n),NRMSE=nrmse,RMSE=rmse,R2=r2,adj.R2=adfR2,mean.abs.error.ratio=mean.abs.error.ratio,med.abs.error.ratio=med.abs.error.ratio,perc80.abs.error.ratio=perc80.abs.error.ratio))
  ### ajouter error et error ratio au return pour pouvoir faire les graphes, etc. 
}
#########
## Calculate R2 (coef of determination / part of explained variance) from the GLM regression
#########
betterGenericR2calculator<-function(dataset,targetName,independantVariableNames){
  dataset2=na.omit(dataset[,c(targetName,independantVariableNames)])
  numVars=colnames(dataset2)[unlist(lapply(dataset2,is.numeric))&colnames(dataset2)%in%independantVariableNames]
  factorVars=colnames(dataset2)[(!unlist(lapply(dataset2,is.numeric)))&colnames(dataset2)%in%independantVariableNames]
  if(length(factorVars)>0&length(numVars)>0){
    factorVarPasted=droplevels(as.factor(apply(cbind(rep("",nrow(dataset2)),as.data.frame(dataset2[,factorVars])),1,paste,collapse=":")))
    theformula=paste(targetName,paste(numVars,collapse = "*"), sep='~')
    nbNumVars=length(numVars)
    resList=by(dataset2, factorVarPasted, FUN=function(x){m=lm(theformula,data=x,y=T); return(list(pred=m$fitted.values,actual=m$y))})
    pred=unlist(lapply(resList,function(x){x$pred}))
    actual=unlist(lapply(resList,function(x){x$actual}))
    p=((length(levels(droplevels(as.factor(factorVarPasted))))-1)*nbNumVars)+(length(levels(droplevels(as.factor(factorVarPasted))))-1)+nbNumVars+1
    res=prediction_evaluator_with_p(pred,actual,p)
  }else if(length(factorVars)==0&length(numVars)>0){
    theformula=paste(targetName,paste(numVars,collapse = "*"), sep='~')
    nbNumVars=length(numVars)
    m=lm(theformula,data=dataset2,y=T)
    pred=m$fitted.values
    actual=m$y
    p=nbNumVars+1
    res=prediction_evaluator_with_p(pred,actual,p)
  }else if(length(factorVars)>0&length(numVars)==0){
    factorVarPasted=droplevels(as.factor(apply(cbind(rep("",nrow(dataset2)),as.data.frame(dataset2[,factorVars])),1,paste,collapse=":")))
    m=lm(dataset2[,targetName]~factorVarPasted,y=T)
    pred=m$fitted.values
    actual=m$y
    p=length(levels(factorVarPasted))
    res=prediction_evaluator_with_p(pred,actual,p)
  }else{
    res=NULL
  }
  return(res)
}
###################
###### Determine the best predictor set (continuous and factor independant variables) to consider for a continuous dependant variable
###################
genericBestPredictor<-function(dataset,targetName,independantVariableNames, plot=T, text=T, las=1){
  ordered_best_additional_predictors=list()
  ordered_best_predictors_per_level=list(NULL)
  ordered_best_r2=list()
  for (i in 1:length(independantVariableNames)){
    level_i_predictors=as.list(independantVariableNames)[!as.list(independantVariableNames)%in%ordered_best_additional_predictors]
    varExp_i=lapply(level_i_predictors,function(x){betterGenericR2calculator(dataset,targetName,c(unlist(ordered_best_additional_predictors),x))$R2})
    if(i==1){
      bivariateR2<-varExp_i
      names(bivariateR2)<-unlist(level_i_predictors)
    }
    ordered_best_additional_predictors=c(ordered_best_additional_predictors,level_i_predictors[varExp_i%in%max(unlist(varExp_i))])
    ordered_best_predictors_per_level=c(ordered_best_predictors_per_level,paste(unlist(ordered_best_predictors_per_level[i]),unlist(ordered_best_additional_predictors[i]), sep=":"))
    ordered_best_r2=c(ordered_best_r2,max(unlist(varExp_i)))
    ordered_r2_progress=c(round(unlist(ordered_best_r2)[1],2),paste(rep("+",length(ordered_best_r2)-1),round(unlist(ordered_best_r2)[-1]-unlist(ordered_best_r2)[-length(ordered_best_r2)],2)))
  }
  ordered_best_predictors_per_level=ordered_best_predictors_per_level[-1]
  
  mynames=unlist(ordered_best_additional_predictors)
  mynames=c(mynames[1],paste("+",mynames[2:length(mynames)]))
  names(ordered_best_r2)<-mynames
  
  if(plot){
    #barplot(unlist(ordered_best_r2), names.arg = unlist(ordered_best_predictors_per_level),las=las,ylab="R2",main=paste("Correlation with",targetName))
    barplot(unlist(ordered_best_r2), names.arg = mynames, las=las, ylab="R2",main=paste("Correlation with",targetName))
    text(y=0.1, x=((1:length(mynames))-0.4)*1.2,labels = ordered_r2_progress)
  }
  if(text) return(list(bivariateR2=bivariateR2,orderedBestR2=ordered_best_r2,orderedBestPredictorsPerLevel=ordered_best_predictors_per_level,orderedBestAdditionalPredictors=ordered_best_additional_predictors, targetName=targetName))
}
####################