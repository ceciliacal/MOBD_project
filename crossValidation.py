from collections import Counter

import numpy as np
import sklearn.model_selection as model_selection
import sklearn.metrics as metrics
import sklearn.svm as svm
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from sklearn.metrics import f1_score, classification_report

from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier


def cross(train_x, test_x, train_y, test_y, classifier):

    if classifier == 'MLP':
        clf = mlp(n_folds=5, metric='f1_macro')
    if classifier == 'KNeighbors':
        clf = kNeighbors(n_folds=5, metric='f1_macro')
    if classifier == 'SVC':
        clf = supportVector(n_folds=5, metric='f1_macro')
    if classifier == 'DecisionTree':
        clf = decisionTree(n_folds=5, metric='f1_macro')
    if classifier == 'RandomForest':
        clf = randomForest(n_folds=5, metric='f1_macro')
    if classifier == 'QuadraticDiscriminantAnalysis':
        clf = quadraticDiscriminantAnalysis(n_folds=5, metric='f1_macro')

    clf.fit(train_x.data, train_y.data.ravel())
    best_parameters = clf.best_params_
    print("\n\nbest_parameters " + classifier + ": ", best_parameters)
    best_result = clf.best_score_
    print("best_result " + classifier + ": ", best_result)

    evaluate_classifier(clf, test_x, test_y)


def quadraticDiscriminantAnalysis(n_folds, metric):

    classifier = QuadraticDiscriminantAnalysis()

    parameters = {
        'reg_param': (1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-9, 1e-10),
        'store_covariance': [True, False],
        'tol': (1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-9, 1e-10),
    }

    clf = model_selection.GridSearchCV(classifier, parameters, scoring=metric, cv=n_folds, n_jobs=-1)

    return clf


def kNeighbors(n_folds, metric):
    classifier = KNeighborsClassifier()

    param_grid = {
        'n_neighbors': np.arange(1, 10),
        'weights': ['uniform', 'distance'],
        'leaf_size': (20, 40, 1),
        'p': (1, 2),
        'algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute']
    }
    clf = model_selection.GridSearchCV(classifier, param_grid, scoring=metric, cv=n_folds, refit=True, n_jobs=-1)

    return clf



def randomForest(n_folds, metric):
    classifier = RandomForestClassifier()

    # griglia degli iperparametri per GridSearch
    param_grid = {
        'criterion': ['gini', 'entropy'],
        'max_depth': np.arange(10, 100, 10),
        'max_features': ['auto', 'sqrt', 'log2'],
        'min_samples_leaf': [1, 2, 3, 4],
        'n_estimators': [1000, 1500, 2000, 2500],
        'bootstrap': [True, False]
    }

    clf = model_selection.GridSearchCV(classifier, param_grid=param_grid, scoring=metric, cv=n_folds, refit=True, n_jobs=-1)

    return clf


def supportVector(n_folds, metric):
    # griglia degli iperparametri\n",
    c1 = [1, 1.5, 2, 2.5, 2.75, 3, 3.5, 5, 10]
    gamma1 = [0.03, 0.05, 0.07, 0.1, 0.5]

    c2 = 10. ** np.arange(-3, 3)
    gamma2 = 10. ** np.arange(-5, 4)

    c3 = 2. ** np.arange(-5, 5)

    param_grid = [
        {'kernel': ['rbf'], 'gamma': [1e-3, 1e-4], 'C': [0.1, 1, 10]},
        {'kernel': ['linear'], 'C': [0.1, 1, 10]},
        {'kernel': ['rbf'], 'gamma': 2. ** np.arange(-3, 3), 'C': 2. ** np.arange(-5, 5),
         'class_weight': [None, 'balanced']},
        {'kernel': ['rbf'], 'gamma': [0.01], 'C': [50], 'class_weight': [None]},
        {'kernel': ['rbf'], 'gamma': gamma2, 'C': c2, 'class_weight': [None, 'balanced']},
        {'kernel': ['rbf'], 'gamma': gamma1, 'C': c1, 'class_weight': [None, 'balanced']},
        {'kernel': ['linear'], 'C': c1},
        {'kernel': ['linear'], 'C': c2},
        {'kernel': ['linear'], 'C': c3}
    ]

    clf = model_selection.GridSearchCV(svm.SVC(), param_grid, scoring=metric, cv=n_folds, refit=True,  n_jobs=-1)

    return clf


def decisionTree(n_folds, metric):
    classifier = (DecisionTreeClassifier())

    param_grid = {
        'criterion': ['gini', 'entropy'],
        'splitter': ['best', 'random'],
        'max_leaf_nodes': np.arange(2, 100),
        'min_samples_split': [2, 3, 4],
        'max_depth': [4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20, 30, 40, 50, 70, 90, 120, 150]
    }

    clf = model_selection.GridSearchCV(classifier, param_grid, scoring=metric, cv=n_folds, refit=True,  n_jobs=-1)

    return clf


def mlp(n_folds, metric):
    classifier = MLPClassifier(max_iter=500)

    param_grid = {
        'hidden_layer_sizes': [(20, 20, 20), (50, 100, 50), (200, 150, 200)],
        'activation': ['relu', 'tanh'],
        'learning_rate': ['constant', 'invscaling', 'adaptive'],
        'alpha': [0.5, 1, 1.5],
        'learning_rate_init': [0.02, 0.01, 0.001],
        'solver': ['sgd'],
        'epsilon': [1e-7, 1e-8, 1e-9]
    }

    print("param_grid : ", param_grid)

    clf = model_selection.GridSearchCV(classifier, param_grid, scoring=metric, cv=n_folds, refit=True, n_jobs=-1)

    return clf




# utilizziamo ora il miglior modello ottenuto al termine della cross-validation per fare previsioni sui dati di test\n",
def evaluate_classifier(classifier, test_x, test_y):

    pred_y = classifier.predict(test_x.data)
    confusion_matrix = metrics.confusion_matrix(test_y.data, pred_y)
    print(confusion_matrix)
    f1_score = metrics.f1_score(test_y.data, pred_y, average='macro')
    acc_score = metrics.accuracy_score(test_y.data, pred_y)
    print('F1: ', f1_score)
    print('Accuracy: ', acc_score)
    report = classification_report(test_y.data, pred_y)
    print(report)


def main():
    print("evaluate")


if __name__ == '__main__':
    main()
