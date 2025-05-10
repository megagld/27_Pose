import matplotlib.pyplot as plt
import numpy as np

#define predictor and response variables
x = np.array([2, 3, 4, 5, 6, 7, 7, 8, 9, 11, 12])
y = np.array([18, 16, 15, 17, 20, 23, 25, 28, 31, 30, 29])

#create scatterplot to visualize relationship between x and y
plt.scatter(x, y)


from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

#specify degree of 3 for polynomial regression model
#include bias=False means don't force y-intercept to equal zero
poly = PolynomialFeatures(degree=3, include_bias=False)

#reshape data to work properly with sklearn
poly_features = poly.fit_transform(x.reshape(-1, 1))

#fit polynomial regression model
poly_reg_model = LinearRegression()
poly_reg_model.fit(poly_features, y)

#display model coefficients
print(poly_reg_model.intercept_, poly_reg_model.coef_)


#use model to make predictions on response variable
y_predicted = poly_reg_model.predict(poly_features)

#create scatterplot of x vs. y
plt.scatter(x, y)

#add line to show fitted polynomial regression model
plt.plot(x, y_predicted, color='purple')