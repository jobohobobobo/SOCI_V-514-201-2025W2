#--------------------------------------------------------------------#
#  Lab 3:  Matrices and Multiple regression                          #
#                                                                    #
#  In this lab we will learn how to create matrices                  #
#  and cover various matrix operations.  We also                     #
#  look at multivarite regression.	                    	     #
#                                                                    #
#--------------------------------------------------------------------#

#  Lets start with creating some vectors.


#--------------------------------------------------------------------#
#                             VECTORS                                #
#--------------------------------------------------------------------#

x0 <- c(1, 5, 2, 8)  # c() concatenates the arguments

#is it really a vector?
is.vector(x0)

x1 <- rep(1, times = 25)  # repeat "1", 25 times
x1

x2 <- seq(from = 1, to = 125, by = 5) # sequence from 1 to 125 counting by 5's
x2

x2[10]    # returns the 10th element in x2
x2[12:22] # returns the 12th element to the 22nd element
x2[10:1]  # returns the 10th element to the 1st
x2[x2 > mean(x2)]  # returns the elements in x2 that are larger than the mean of x2

x3 <- ((x2^2) - 4)/(3 + log(x2)) # we can use mathematical arguments
# to assign objects a vector,  
# matrix, list, etc.
x3

x4 <- 1:25 # integers 1 to 25, same as seq(), but it counts by 1's
x4

#can also assign variables based on R functions, such as "rnorm"
x4 <- rnorm(n = 25, mean = 10, sd = 2) # random normal variable
# with length = 25, mean=10, sd=2
# note: we have written over the old x4
x4

hist(x4)  # is it really normal?  Note that the larger n is,
# the more normal it will look.


#--------------------------------------------------------------------#
#                             MATRICES                               #
#--------------------------------------------------------------------#

X1 <- cbind(x1, x2, x3, x4) # combine these vectors by columns,
# rbind() connects them by rows

X1			#notice that R is case sensitive
x1 


is.matrix(X1) # is it really a matrix?

X2 <- matrix(x2, ncol = 5) # another way to make a matrix, the "ncol" option
# specifies the number of columns;
# nrow is another option,
# to see them all check out help(matrix)
X2


#some helpful functions for looking at dimensions of matrix
dim(X2)   # dimensions of mat2 (rows are given first, followed by columns)
nrow(X2)  # number of rows
ncol(X2)  # number of columns

# Some useful ways for looking at elements in a matrix
X2[1,2]  # element in the first row, second column
X2[,2]   # returns the second column
X2[,2:4] # returns columns 2, 3, and 4
X2[1,]   # returns the first row



#--------------------------------------------------------------------#
#                         MATRIX OPERATIONS                          #
#--------------------------------------------------------------------#

# Addition, sub, mult, and div by a scalar takes
# each element of the matrix and performs the
# operation with the scalar
X1
X1 + 2
X1 - 2
X1 * 2
X1 / 2

# Addition and subtraction between matrices is
# similar, but they must have the same dimensions
X1 + X1
X1 + X2  # Why doesn't this work?

# Multiplication is a little different...
dim(X1)
X3 <- matrix(rnorm(16), nrow = 4, ncol = 4)
X3

X4 <- X1 %*% X3		#  the sign for matrix multiplication:  %*%
dim(X4)
nrow(X1)  # X4 should have the same number of rows as X1
ncol(X3)  # and the same number of columns as X3

X3 %*% X1 # but can't go the other way

t(X1)      # Transpose of a matrix 
dim(X1)
dim(t(X1))

X1.t.X1 <- t(X1) %*% X1    # (X'X)
inv.X1t <- solve(X1.t.X1)  # Inverse (only works for square matrices,
# i.e. nrow = ncol)


#Matrix operations and OLS regresion

X<-X1 				#let's consider this the design matrix
y<- rnorm(n = 25, mean = 10, sd = 2)  #the dependent variable

#recall that in matrix notation, OLS is (X'X)^-1 * X'y)

X.t.X <- t(X) %*% X 	   	# (X'X)
inv.Xt <- solve (X.t.X)  	# (X'X)^-1
X.t.y <- t(X) %*% y  		# (X'y)
inv.Xt %*% X.t.y		# (X'X)^-1 * X'y


#regress y on X1 using lm function
Xdata <- as.data.frame (X)			#first need to make X1 a data frame
model1 <- lm (y ~ x2 + x3 + x4, data=Xdata)	#estimate model; be sure to exclude x1
#because it is the intercept
summary(model1)			#compare these results to those using matrix algebra

## If looking for extra challenge:

## How might we find the error variance of the regression?  
## What about the standard error of the Beta estimates?

Bhats<-inv.Xt %*% X.t.y	#assign (X'X)^-1 * X'y) to Bhat object
e<-y-(X%*%Bhats)	#solve for e, as e = y-XB
SSR<-t(e)%*%e		#compute SSR (e'e)
sigma2<-SSR/(25-3-1)	#compute sigma-squared (SSR/n-k-1)
sigma2			

is.matrix(sigma2)	#sigma2 is a matrix, so must convert to scalar
sigma2<-c(sigma2)	

Vb<-sigma2 * (inv.Xt)	#compute Variance of Betas (sigma2 * (X'X)-1)  
# This produces a variance-covariance matrix.
Vb			# Variance of the Betas are on the main diagnol

sqrt(diag(Vb))		#Take the square root to get the standard errors of the Betas

summary(model1)		#Compare with the lm output to see if the standard errors match



#--------------------------------------------------------------------#
#   		Helpful R Code for Homework	                     #
#--------------------------------------------------------------------#


#Reading Data into R

x<-c(1,1,1,1,1,1,1,1,1,3,0,3,4,1,1,2,5,0,4,1,9,3,2,0,6,0,7)	#read in vector of x's
X<-matrix(x, ncol=3, nrow=9)					#put the vector x into a matrix X

y<-c(3,4,5,0,1,2,2,4,1)		#read in vector of y's




## Performing a linear regression analysis 

# Be sure to change your file directory.  File -> Change dir

dir()      # see if the data is in the working directory
oecd <- read.table("oecd.txt")  # load the oecd data

# The function for linear regression is lm(y ~ x1 + x2).
# See help(lm) for for more details.  




