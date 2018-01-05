# -----------------------------------------------------------------------------
# title: Boosted Boxplots
# description: add several useful features to the classical R boxplot function
# author: Alassane Samba (alassane.samba@orange.com)
# Copyright (c) 2016 Orange
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# -----------------------------------------------------------------------------
boostedBoxplot<-function(y,x, main="", labx=NULL,laby=NULL, plot.mean=T, text.freq=T, las=1, ylim=c(0,0), limitVisibleModalities=30, decreasing=NULL, dynamic=F){
  xlab=""
  if(is.null(labx))labx=deparse(substitute(x))
  if(is.null(laby))laby=deparse(substitute(y))
  if(main==""){
  main=labx
  }else{
  xlab=labx
  }
  x=droplevels(as.factor(x))
  p=length(levels(as.factor(x)))
  if(!is.null(decreasing)){
    x=factor(x,levels = names(sort(tapply(y,x,median), decreasing = decreasing)), ordered = F)
  }else{
    decreasing=T
  }
  #limitVisibleModalities
  if(limitVisibleModalities<p-1){
    x=factor(x,levels = names(sort(tapply(y,x,median), decreasing = decreasing)), ordered = F)
    lx=levels(as.factor(x))
    leftl=lx[1:floor(limitVisibleModalities/2)]
    rightl=lx[(p-floor(limitVisibleModalities/2)+1):p]
    n_other=length(lx[!lx%in%c(leftl,rightl)])
    x=as.character(x)
    x[!x%in%c(leftl,rightl)]<-paste(c("other(",n_other,")"),collapse="")
    x=as.factor(x)
    x=factor(x,levels = names(sort(tapply(y,x,median), decreasing = decreasing)), ordered = F)
  }
  #dynamicity
  if(dynamic){
    dataf=data.frame(Y=y,X=x)
    require(rAmCharts)
    amBoxplot(Y~X,data=dataf,labelRotation = (las==2)*90, ylab = laby, main = main)
  }else{
  if(sum(ylim)==0){
    rb<-boxplot(y~x, main=main, xlab=xlab, ylab=laby, las=las)
    grid()
    #rb<-boxplot(y~x, main=main, xlab=xlab, ylab=laby, las=las, add=T)
  }else{
    rb<-boxplot(y~x, main=main, xlab=xlab, ylab=laby, las=las, ylim=ylim)
    grid()
    #rb<-boxplot(y~x, main=main, xlab=xlab, ylab=laby, las=las, add=T)
  }
  if(plot.mean){
    mn.t <- tapply(y, x, mean, na.rm=T)
    sd.t <- tapply(y, x, sd, na.rm=T)
    xi <- 0.3 + seq(rb$n)
    points(xi, mn.t, col = "red", pch = 18, cex=1)
    arrows(xi, mn.t - sd.t, xi, mn.t + sd.t,code = 3, col = "red", angle = 75, length = .1, lwd = 1)
  }
  if(text.freq)text(x=1:length(rb$names), y=(rb$stats[3,]+rb$stats[4,])/2,label=rb$n)
  }
}
############