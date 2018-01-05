# ----------------------------------------------------------------------
# title: TOM R API
# description: Machine Learning-Based Test Results Analysis
# author: Alassane Samba (alassane.samba@orange.com)
# Copyright (c) 2017 Orange
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ----------------------------------------------------------------------
# Load useful fonctions
source("R/explainer.R")
source("R/boostedBoxPlot.R")
# init
tomData<-NULL
tomAnalysis<-NULL
#* Read new file (to change to post)
#* @get /read
tomRead<-function(file,res){
  file_ok <- as.character(file)
  if (is.na(file_ok)){
    res$status <- 400
    res$body <- "val parameter must be a number"
    return(res)
  }
  st=Sys.time()
  tomData<<-read.table(file = file_ok, sep=',', header=TRUE, quote = "\"", comment.char = "")
  et=Sys.time()
  #save(tomData,file = "tom.rdata")
  list(result="success", durationInSeconds=as.numeric((et-st), units = "secs"))
}
#* Analyze correlations
#* @get /analyze
tomAnalyze<-function(input="pod_name:deploy_scenario:version:runner_id",output="bandwidth.MBps.",res){
  if(is.null(tomData)){
    res$status <- 400
    res$body <- "please read data first : url/read"
    return(res)
  }
  input_ok<-as.character(input)
  input_ok<-unlist(strsplit(input_ok,split = ":"))
  if(sum(is.na(input_ok))>0){
    res$status <- 400
    res$body <- "input parameter must be a string including data context parameters separatd by a double dot (:)"
    return(res)
  }
  if(sum(!input_ok%in%colnames(tomData))==length(input_ok)){
    res$status <- 400
    res$body <- "input parameter items must all be inluded in data header"
    return(res)
  }
  output_ok <- as.character(output)
  if(is.na(output_ok)){
    res$status <- 400
    res$body <- "output parameter must be a string inluded in data header"
    return(res)
  }
  if(!output_ok%in%colnames(tomData)){
    res$status <- 400
    res$body <- "output parameter must be inluded in data header"
    return(res)
  }
  st=Sys.time()
  tomAnalysis<<-genericBestPredictor(dataset = tomData, targetName = output_ok, independantVariableNames = input_ok, plot = F)
  et=Sys.time()
  list(result="success", durationInSeconds=as.numeric((et-st), units = "secs"))
}
#* Get bivariate R2 values
#* @get /correlation
tomBivariateR2<-function(res){
  if(is.null(tomAnalysis)){
    res$status <- 400
    res$body <- "please analyze data first : url/analyze"
    return(res)
  }
  return(as.list(tomAnalysis$bivariateR2))
}
#* Get bivariate R2 values
#* @get /explain
tomExplain<-function(res){
  if(is.null(tomAnalysis)){
    res$status <- 400
    res$body <- "please analyze data first : url/analyze"
    return(res)
  }
  return(as.list(tomAnalysis$orderedBestR2))
}
#* Get bivariate R2 values
#* @png
#* @get /explainGraph
tomExplainGraph<-function(res){
  if(is.null(tomAnalysis)){
    res$status <- 400
    res$body <- "please analyze data first : url/analyze"
    return(res)
  }
  maxmargin=20
  bottomheigth=0.5*max(nchar(names(tomAnalysis$orderedBestR2)),na.rm=T)
  if(bottomheigth>maxmargin) bottomheigth<-maxmargin
  op=par(mar=c(bottomheigth, 4.1, 4.1, 2.1))
  barplot(unlist(tomAnalysis$orderedBestR2), names.arg = names(tomAnalysis$orderedBestR2), las=2, ylab="R squared correlation coef.",main=paste("Correlation with",tomAnalysis$targetName))
  par(op)
}
#* Get the head contexts cases having highest KPI values
#* @get /head
tomHead<-function(input="pod_name",output="bandwidth.MBps.",limit=5,res){
  if(is.null(tomData)){
    res$status <- 400
    res$body <- "please read data first : url/read"
    return(res)
  }
  input_ok<-as.character(input)
  input_ok<-unlist(strsplit(input_ok,split = ":"))
  if(sum(is.na(input_ok))>0){
    res$status <- 400
    res$body <- "input parameter must be a string including data context parameters separatd by a double dot (:)"
    return(res)
  }
  if(sum(!input_ok%in%colnames(tomData))==length(input_ok)){
    res$status <- 400
    res$body <- "input parameter items must all be inluded in data header"
    return(res)
  }
  output_ok <- as.character(output)
  if(is.na(output_ok)){
    res$status <- 400
    res$body <- "output parameter must be a string inluded in data header"
    return(res)
  }
  if(!output_ok%in%colnames(tomData)){
    res$status <- 400
    res$body <- "output parameter must be inluded in data header"
    return(res)
  }
  limit=as.integer(limit)
  if(is.na(limit)){
    res$status <- 400
    res$body <- "limit parameter must be an integer"
    return(res)
  }
  varFactor=apply(as.data.frame(tomData[,input_ok]),1,paste,collapse=":")
  sorted=sort(tapply(tomData[,output_ok],varFactor,median, na.rm=T),decreasing = TRUE)[1:limit]
  return(as.list(sorted))
}
#* Get the tail contexts cases having lowest KPI values
#* @get /tail
tomTail<-function(input="pod_name",output="bandwidth.MBps.",limit=5,res){
  if(is.null(tomData)){
    res$status <- 400
    res$body <- "please read data first : url/read"
    return(res)
  }
  input_ok<-as.character(input)
  input_ok<-unlist(strsplit(input_ok,split = ":"))
  if(sum(is.na(input_ok))>0){
    res$status <- 400
    res$body <- "input parameter must be a string including data context parameters separatd by a double dot (:)"
    return(res)
  }
  if(sum(!input_ok%in%colnames(tomData))==length(input_ok)){
    res$status <- 400
    res$body <- "input parameter items must all be inluded in data header"
    return(res)
  }
  output_ok <- as.character(output)
  if(is.na(output_ok)){
    res$status <- 400
    res$body <- "output parameter must be a string inluded in data header"
    return(res)
  }
  if(!output_ok%in%colnames(tomData)){
    res$status <- 400
    res$body <- "output parameter must be inluded in data header"
    return(res)
  }
  limit=as.integer(limit)
  if(is.na(limit)){
    res$status <- 400
    res$body <- "limit parameter must be an integer"
    return(res)
  }
  varFactor=apply(as.data.frame(tomData[,input_ok]),1,paste,collapse=":")
  sorted=sort(tapply(tomData[,output_ok],varFactor,median,na.rm=T),decreasing = FALSE)[1:limit]
  return(as.list(sorted))
}
#* Get the comparison graph
#* @png
#* @get /comparGraph
tomComparGraph<-function(input="pod_name",output="bandwidth.MBps.",limit=10,plotmean=TRUE,textfreq=TRUE,res){
  if(is.null(tomData)){
    res$status <- 400
    res$body <- "please read data first : url/read"
    return(res)
  }
  input_ok<-as.character(input)
  input_ok<-unlist(strsplit(input_ok,split = ":"))
  if(sum(is.na(input_ok))>0){
    res$status <- 400
    res$body <- "input parameter must be a string including data context parameters separatd by a double dot (:)"
    return(res)
  }
  if(sum(!input_ok%in%colnames(tomData))==length(input_ok)){
    res$status <- 400
    res$body <- "input parameter items must all be inluded in data header"
    return(res)
  }
  output_ok <- as.character(output)
  if(is.na(output_ok)){
    res$status <- 400
    res$body <- "output parameter must be a string inluded in data header"
    return(res)
  }
  if(!output_ok%in%colnames(tomData)){
    res$status <- 400
    res$body <- "output parameter must be inluded in data header"
    return(res)
  }
  limit=as.integer(limit)
  if(is.na(limit)){
    res$status <- 400
    res$body <- "n parameter must be an integer"
    return(res)
  }
  varFactor=as.factor(apply(as.data.frame(tomData[,input_ok]),1,paste,collapse=":"))
  maxmargin=20
  bottomheigth=0.5*max(nchar(levels(varFactor)),na.rm=T)
  if(bottomheigth>maxmargin) bottomheigth<-maxmargin
  leftwidth=0.5*nchar(as.character(max(tomData[,output_ok],na.rm=T)))
  if(leftwidth>maxmargin) leftwidth<-maxmargin
  op=par(mar=c(bottomheigth, leftwidth+1, 4.1, 2.1))
  boostedBoxplot(tomData[,output_ok],varFactor,decreasing=T,las=2,main=input,laby="",labx="",limitVisibleModalities=limit,dynamic=F,plot.mean=plotmean, text.freq=textfreq)
  title(ylab = output_ok, line = leftwidth)
  par(op)
}
# # to run it, do:
# library(plumber)
# r<-plumb("tom.r")
# r$run(port=8000)
