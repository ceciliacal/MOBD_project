import bisect
import pickle
from collections import Counter

import sklearn
import sklearn.preprocessing as prep
import numpy as np
import pandas as pd
import seaborn as sns
import missingno as msno
import plotly.express as px
from imblearn.ensemble import BalancedBaggingClassifier
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler, NearMiss, CondensedNearestNeighbour, TomekLinks, \
    ClusterCentroids, EditedNearestNeighbours, OneSidedSelection, NeighbourhoodCleaningRule, \
    RepeatedEditedNearestNeighbours, AllKNN, InstanceHardnessThreshold
from matplotlib import pyplot as plt
from sklearn.experimental import enable_iterative_imputer

from scipy.stats import stats
from sklearn.covariance import EllipticEnvelope, EmpiricalCovariance, MinCovDet
from sklearn.decomposition import PCA, TruncatedSVD, NMF, FactorAnalysis, FastICA, IncrementalPCA, SparsePCA, \
    MiniBatchSparsePCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import IsolationForest
from sklearn.feature_selection import VarianceThreshold, RFE, SelectKBest, mutual_info_classif, f_classif, \
    SelectFromModel
from sklearn.impute import KNNImputer, SimpleImputer, IterativeImputer
from sklearn.linear_model import LogisticRegression
from sklearn.manifold import Isomap, LocallyLinearEmbedding
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier, RadiusNeighborsRegressor, LocalOutlierFactor, \
    RadiusNeighborsClassifier, NearestCentroid
from sklearn.preprocessing import MaxAbsScaler, RobustScaler, PowerTransformer, QuantileTransformer, Normalizer, \
    LabelEncoder
from sklearn.svm import OneClassSVM

import crossValidation
from sklearn.cluster import DBSCAN, KMeans
from matplotlib import cm
import winsound



class Dataset:
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.naCount = None
        self.outliers = None  # lista outliers di una colonna
        self.dataColumn = None  # elementi di una colonna
        self.result = None
        self.outliersDict = {}  # { F1: [meanNA, meanZSCORE, stdZSCORE, resultOUTLIERS]


def preProcessing(train_x, test_x, train_y, test_y, x, y, na_method, find_method, substitute_method, scale_type):
    train_x.data, test_x.data, train_y.data, test_y.data = sklearn.model_selection.train_test_split(x, y, test_size=0.2,
                                                                                                    random_state=42)
    print('Train:', train_x.data.shape, train_y.data.shape)
    print('Test:', test_x.data.shape, test_y.data.shape)

    # traformo train_x.data da numpy.ndarray in un DataFrame
    # altrimenti non si può utilizzare attributo .isna() nella def get_na_count()
    train_x.data = pd.DataFrame(train_x.data)
    test_x.data = pd.DataFrame(test_x.data)
    train_y.data = pd.DataFrame(train_y.data, columns=['CLASS'])
    test_y.data = pd.DataFrame(test_y.data, columns=['CLASS'])

    # aggiungiamo i nomi alle colonne in tutti e 4 i data frames
    changeColNames(train_x.data)
    changeColNames(test_x.data)

    # Sostituiamo i valori mancanti (NaN) del train e test con opportuni valori
    naDetection(train_x, test_x, na_method)

    # outliers detection
    if find_method == "DBSCAN":
        # dbScan(train_x)
        isoFor(train_x, test_x)

    else:
        outlierDetection(train_x, test_x, train_y, find_method, substitute_method)

    # dbScan(train_x, train_y)
    # dbScan(test_x, test_y)

    box = plt.boxplot(train_x.data, notch=True, patch_artist=True)
    plt.suptitle("After detecting outliers with IQR and KNN")
    colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'pink', 'blue', 'green',
              'purple', 'red', 'C10', 'C4', 'C3', 'C6', 'C1', 'C2', 'C9', 'C5', 'yellow',
              'magenta', 'C19']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)

    plt.show()

    # normalizziamo i dati
    scale(train_x, test_x, train_y, test_y, scale_type)
    # plotScalers(train_x, test_x)
    # dbScan(train_x)
    np.savetxt("train_x.PAIRPLOT.csv", train_x.data, delimiter=",")
    datasetPath = './train_x.PAIRPLOT.csv'
    dataset = pd.read_csv(datasetPath)
    # dataset = sns.load_dataset('train_x.PAIRPLOT.csv')

    # sns.pairplot(dataset)
    # plt.show()

    # applichiamo PCA
    pca(train_x, test_x)

    '''
    fs = SelectKBest(score_func=mutual_info_classif, k=13)
    # fs = SelectKBest(score_func=f_classif, k='all')

    fs.fit(train_x.data, train_y.data.ravel())
    train_x.data = fs.transform(train_x.data)
    test_x.data = fs.transform(test_x.data)
    '''
    # SMOTE

    '''
    # Under-sampling:
    ros = RandomUnderSampler(random_state=42)
    #ros = RandomOverSampler(random_state=42)

    (train_x.data, train_y.data) = ros.fit_sample(train_x.data, train_y.data)
    (test_x.data, test_y.data) = ros.fit_sample(test_x.data, test_y.data)
    '''

    # define the undersampling method
    # undersample = TomekLinks()
    # undersample =EditedNearestNeighbours(n_neighbors=1)
    # undersample = NeighbourhoodCleaningRule(n_neighbors=2, threshold_cleaning=0.5)
    # undersample = NeighbourhoodCleaningRule(n_neighbors=2,threshold_cleaning=0)

    # migliori
    # undersample = RepeatedEditedNearestNeighbours(n_neighbors=6, max_iter = 900000, kind_sel = 'mode', n_jobs = -1)
    # undersample = NeighbourhoodCleaningRule(n_neighbors=10,threshold_cleaning=0, n_jobs = -1,  kind_sel = 'mode')
    # undersample =EditedNearestNeighbours(n_neighbors=10, kind_sel = 'mode', n_jobs = -1)

    Resampling(train_x, train_y)

    # oversample = ADASYN (random_state=42)  # migliore!!!!
    # undersample =InstanceHardnessThreshold(random_state=42)

    # transform the dataset
    # train_x.data, train_y.data = oversample.fit_resample(train_x.data, train_y.data)
    # test_x.data, test_y.data = undersample.fit_resample(test_x.data, test_y.data)
    ''' 
    train_y.data = LabelEncoder().fit_transform(train_y.data)
    counter = Counter(train_y.data)
    for k, v in counter.items():
        per = v / len(train_y.data) * 100
        print('Class=%d, n=%d (%.3f%%)' % (k, v, per))

    oversample = SMOTE()
    train_x.data, train_y.data = oversample.fit_resample(train_x.data, train_y.data)

    undersample = RepeatedEditedNearestNeighbours(n_neighbors=10, max_iter = 900000, kind_sel = 'mode', n_jobs = -1)

    #undersample =AllKNN(allow_minority=True, n_neighbors=7, kind_sel = 'mode', n_jobs = -1) #migliore!!!!
    train_x.data, train_y.data = undersample.fit_resample(train_x.data, train_y.data)

    #undersample =InstanceHardnessThreshold(random_state=42)


    # transform the dataset
    #train_x.data, train_y.data = undersample.fit_resample(train_x.data, train_y.data)
    #test_x.data, test_y.data = undersample.fit_resample(test_x.data, test_y.data)

    counter = Counter(train_y.data)
    for k, v in counter.items():
        per = v / len(train_y.data) * 100
        print('Class=%d, n=%d (%.3f%%)' % (k, v, per))
    '''
    '''
    oversample = SMOTE()
    train_x.data, train_y.data = oversample.fit_resample(train_x.data, train_y.data)
    counter = Counter(train_y.data)
    for k,v in counter.items():
        per = v / len(y) * 100
        print('Class=%d, n=%d (%.3f%%)' % (k, v, per))
    '''

    '''
    #Under-sampling:
    ros = RandomUnderSampler(random_state=0)
    (train_x.data, train_y.data) = ros.fit_sample(train_x.data, train_y.data)
    
    
    #Over-sampling:
    ros = RandomOverSampler(random_state=0)
    (train_x.data, train_y.data) = ros.fit_sample(train_x.data, train_y.data)
    (test_x.data, test_y.data) = ros.fit_sample(test_x.data, test_y.data)
    counter = Counter(test_y.data)
    for k, v in counter.items():
        per = v / len(y) * 100
        print('Class=%d, n=%d (%.3f%%)' % (k, v, per))

    '''


def naDetection(train_x, test_x, na_method):
    if na_method == "MEAN":
        naMean(train_x, test_x)
    if na_method == "KNN":
        naKNN(train_x, test_x)


def zScore(dataset):
    z = np.abs(stats.zscore(dataset.data))
    print(z)
    threshold = 3
    print(np.where(z > 3))
    print(len(np.where(z > 3)[0]))
    return z


def pca(train_x, test_x):
    pca = PCA()
    # pca =MiniBatchSparsePCA(n_components=15, random_state=42, batch_size=50)
    train_x.data = pca.fit_transform(train_x.data)

    if test_x is not None:
        test_x.data = pca.transform(test_x.data)
    ''' 
    explained_variance = pca.explained_variance_ratio_
    count = 0
    for i in explained_variance:
        count = count + 1
        print("explained_variance", count, "--->", i)

    print("explained_variance:", explained_variance)
    '''
    ''' 
    exp_var_cumul = np.cumsum(pca.explained_variance_ratio_)
    fig = px.area(
        x=range(1, exp_var_cumul.shape[0] + 1),
        y=exp_var_cumul,
        labels={"x": "# Components", "y": "Explained Variance"},
    )
    fig.show()
    '''
    exp_var_cumsum = pd.Series(np.round(pca.explained_variance_ratio_.cumsum(), 4) * 100)
    for index, var in enumerate(exp_var_cumsum):
        print('if n_components= %d,   variance=%f' % (index, np.round(var, 3)))

    pca = PCA(n_components=15)
    # pca =MiniBatchSparsePCA(n_components=15, random_state=42, batch_size=50)
    train_x.data = pca.fit_transform(train_x.data)

    if test_x is not None:
        test_x.data = pca.transform(test_x.data)

    save_object(pca, "pca.pkl")


'''
È buona norma normalizzare le feature che utilizzano scale e intervalli diversi.
Non normalizzare i dati rende l'allenamento più difficile e rende il modello risultante
dipendente dalla scelta delle unità nell'input.
'''


def scale(train_x, test_x, train_y, test_y, scale_type):
    matrix(train_x, test_x, train_y, test_y)

    if scale_type == "STANDARD":
        standardScaler(train_x, test_x)
    if scale_type == "MINMAX":
        minMaxScaler(train_x, test_x)
    if scale_type == "MAX_ABS":
        maxAbsScaler(train_x, test_x)
    if scale_type == "ROBUST":
        robustScaler(train_x, test_x)


def Resampling(train_x, train_y):
    train_y.data = LabelEncoder().fit_transform(train_y.data)
    # summarize distribution

    piePlot(train_y, "Before Resampling")

    undersample = AllKNN(allow_minority=True, n_neighbors=7, kind_sel='mode', n_jobs=-1)  # migliore!!!!

    # transform the dataset
    train_x.data, train_y.data = undersample.fit_resample(train_x.data, train_y.data)

    piePlot(train_y, "After Resampling")


def piePlot(train_y, title):
    counter = Counter(train_y.data)

    freq = []
    label = []

    for k, v in counter.items():
        per = v / len(train_y.data) * 100

        # label.append("Class " + str(k))
        bisect.insort(label, "Class " + str(k))
        i = bisect.bisect(label, "Class " + str(k))
        freq.insert(i - 1, per)

        print('Class=%d, n=%d (%.3f%%)' % (k, v, per))

    print("\n\n")

    plt.pie(
        freq,
        labels=label,
        shadow=True,
        # colors=colors,
        startangle=90,
        autopct='%1.1f%%'
    )
    plt.axis('equal')
    plt.tight_layout()
    plt.title(title)
    plt.show()


def matrix(train_x, test_x, train_y, test_y):
    # convertiamo i DataFrame per l'input e per l'output in vettori 2D (matrici)
    train_x.data = np.float64(train_x.data)
    train_y.data = np.float64(train_y.data)
    train_y.data = train_y.data.reshape((len(train_y.data), 1))

    if test_x is not None or test_y is not None:
        test_x.data = np.float64(test_x.data)
        test_y.data = np.float64(test_y.data)
        test_y.data = test_y.data.reshape((len(test_y.data), 1))
        print("MATRIX Y: ", test_x.data.shape, test_y.data.shape)

    print("MATRIX X: ", train_x.data.shape, train_y.data.shape)


def standardScaler(train_x, test_x):
    scaler = prep.StandardScaler()
    scaler.fit(train_x.data)
    train_x.data = scaler.transform(train_x.data)
    save_object(scaler, 'scaler.pkl')

    if test_x is not None:
        test_x.data = scaler.transform(test_x.data)

    print(pd.DataFrame(train_x.data).describe())
    return train_x.data


def minMaxScaler(train_x, test_x):
    # feature_range=(0, 2)
    scaler_x = prep.MinMaxScaler(feature_range=(-1, 1))

    scaler_x.fit(train_x.data)

    train_x.data = scaler_x.transform(train_x.data)

    if test_x is not None:
        test_x.data = scaler_x.transform(test_x.data)

    print(pd.DataFrame(train_x.data).describe())
    return train_x.data


def maxAbsScaler(train_x, test_x):
    scaler = MaxAbsScaler()
    scaler.fit(train_x.data)
    train_x.data = scaler.transform(train_x.data)

    if test_x is not None:
        test_x.data = scaler.transform(test_x.data)

    print(pd.DataFrame(train_x.data).describe())
    return train_x.data


def robustScaler(train_x, test_x):
    scaler = RobustScaler(quantile_range=(25, 75), with_centering=False)
    scaler.fit(train_x.data)
    train_x.data = scaler.transform(train_x.data)

    if test_x is not None:
        test_x.data = scaler.transform(test_x.data)
    return train_x.data


def plotScalers(train_x, test_x):
    dataset = pd.DataFrame(train_x.data)
    for colName in dataset:
        print("colName: ", colName)
        # = 'F1'
        # dataset = pd.DataFrame(train_x.data)
        # print("dataset = ", dataset)
        changeColNames(dataset)
        orig = dataset[colName]
        # print("provaaa:", dataset[colName])
        orig_mean = orig.mean()
        bins = 50
        alpha = 0.5

        # before Scaling
        plt.figure(figsize=(10, 5))
        plt.hist(orig, bins, alpha=alpha, label='Before Scaling', color='C4')
        plt.axvline(orig_mean, color='k', linestyle='dashed', linewidth=1)

        # afterScaling
        dataset2 = pd.DataFrame(standardScaler(train_x, test_x))
        changeColNames(dataset2)
        normalized = dataset2[colName]
        plt.suptitle(colName)
        plt.hist(normalized, bins, alpha=alpha, label='After Scaling', color='lightblue')
        plt.axvline(normalized.mean(), color='k', linestyle='dashed', linewidth=1)
        plt.legend(loc='upper right')

        plt.figure(figsize=(5, 5))

        # g = sns.jointplot(x="median_income", y=scalerName, data=dfX, kind='hex', ratio=3)
        # train_x.data = standardScaler(train_x)
        plt.show()


def plotScalers2(train_x, test_x):
    df = pd.DataFrame(train_x.data)
    changeColNames(df)

    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(6, 5))

    ax1.set_title('Before Scaling')

    for colName in df.columns:
        sns.kdeplot(df[colName], ax=ax1)

    ax2.set_title('After MaxAbs Scaler')
    df = pd.DataFrame(maxAbsScaler(train_x, test_x))
    changeColNames(df)
    for colName in df.columns:
        sns.kdeplot(df[colName], ax=ax2)

    plt.show()


# sostuisce outliers con media per ogni colonna
def outlierMean(train_x, test_x, colName):
    # copio dataset in lista y e tolgo outliers
    y = train_x.data[colName].copy()
    for i in train_x.outliers:
        y = y[y != i]

    mean = y.mean()
    print("\n\n -- Media di ", colName, " : ", mean)
    train_x.result = mean
    appendDict(colName, mean, train_x)
    # train_x.outliersDict[colName] = mean

    if test_x is not None:
        test_x.result = mean


# questa funzione copia in dataColumn tutti gli elementi di una colonna, e per ogni colonna
# si gestiscono gli outlier con metodi opportuni


def outlierMedian(train_x, test_x, colName):
    # copio dataset in lista y e tolgo outliers
    y = train_x.data[colName].copy()
    for i in train_x.outliers:
        y = y[y != i]

    median = y.median()
    print("\n\n -- Media di ", colName, " : ", median)
    train_x.result = median
    appendDict(colName, median, train_x)
    # train_x.outliersDict[colName] = mean

    if test_x is not None:
        test_x.result = median


def outlierDetection(train_x, test_x, train_y, find_method, substitute_method):
    title = 'Before Outliers Detection'

    box = plt.boxplot(train_x.data, notch=True, patch_artist=True)
    plt.suptitle(title)
    colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'pink', 'blue', 'green',
              'purple', 'red', 'C10', 'C4', 'C3', 'C6', 'C1', 'C2', 'C9', 'C5', 'yellow',
              'magenta', 'C19']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)

    plt.show()

    for colName in train_x.data.columns:
        print("\n\ncolName = ", colName)

        title = colName + ' before KNN'
        train_x.data[colName].plot(kind='hist', title=title, color='C4', label="before")
        plt.show

        # metodi diversi per il calcolo di outliers sia per train_x che per test_x
        if find_method == "IQR":
            print("\nOUTLIERS WITH IQR")
            outIQR(train_x, test_x, colName)

        if find_method == "ZSCORE":
            print("\n\nOUTLIERS WITH ZSCORE\n")
            # print("\n------ train ------")
            outliers_train, outliers_test, mean, std = outZSCORE(train_x, test_x, colName)

            appendDict(colName, mean, train_x)
            appendDict(colName, std, train_x)
            # print("\n------ test ------")
            # outZSCORE(test_x,colName)

        if find_method == "DBSCAN":
            print("\n\nOUTLIERS WITH DBSCAN\n")
            print("\n------ train ------")
            dbScan(train_x, colName)
            print("\n------ test ------")
            dbScan(test_x, colName)

        if substitute_method == "KNN":

            # una volta che ho la lista di outliers, li sostituisco con il metodo KNN, che avrà come input sia
            # il training che il test, poichè devo modificarli entrambi colonna x colonna
            knnDetectionTRAIN(train_x, test_x, colName)
            # knnDetectionTRAIN2(train_x,test_x,colName)

        else:
            outlierMean(train_x, test_x, colName)
            # outlierMedian(train_x,test_x,colName)

        # sostuituiamo i risultati con gli outliers nel dataset originario
        substituteOutliers(train_x, colName, find_method, substitute_method)

        print("\n\n--------- KNN TEST ------ ")
        substituteOutliers(test_x, colName, find_method, substitute_method)

        # controllo outliers dopo aver applicato KNN
        checkOutliersAfterReplacement(train_x, test_x, colName, find_method)

        title = colName + ' after KNN'
        train_x.data[colName].plot(kind='hist', title=colName, color='lightgreen')
        plt.show

        plt.show()


def dbScan(dataset_x):
    model = DBSCAN(
        eps=5,
        metric='euclidean',
        min_samples=10,
        n_jobs=-1).fit(dataset_x.data)

    # clusters = model.fit_predict(train_x.data)

    dataset_x.outliers = dataset_x.data[model.labels_ == -1]

    print("model ==== ", model, "\n\n")

    print("outliers ==== ", dataset_x.outliers, "\n\n")
    for colName in dataset_x.outliers.columns:
        for j in dataset_x.outliers[colName]:
            dataset_x.data[colName][dataset_x.data[colName] == j] = np.nan

    getNaCount(dataset_x)

    imputer = KNNImputer(n_neighbors=3)
    imputed = imputer.fit_transform(dataset_x.data)
    dataset_x.data = pd.DataFrame(imputed, columns=dataset_x.data.columns)

    return dataset_x.outliers


def isoFor(dataset_x, dataset_y):
    model = IsolationForest(contamination=0.5)
    yhat = model.fit_predict(dataset_x.data)

    # clusters = model.fit_predict(train_x.data)

    outliers = dataset_x.data[yhat == -1]

    print("model ==== ", model, "\n\n")

    print("outliers ==== ", outliers, "\n\n")
    '''
    for colName in dataset_x.outliers.columns:
        for j in dataset_x.outliers[colName]:
            dataset_x.data[colName][dataset_x.data[colName] == j] = np.nan
    '''

    for colName in outliers.columns:
        print("colName:", colName)
        dataset_x.outliers = []
        for j in outliers[colName]:
            for i in dataset_x.data[colName]:
                if i == j:
                    dataset_x.outliers.append(i)

        y = dataset_x.data[colName].copy()
        for m in dataset_x.outliers:
            # print("i ==== ", i)
            y = y[y != m]

        lenX = len(dataset_x.data[colName]) - len(dataset_x.outliers)
        rows = lenX
        col = 1
        X = [[0 for i in range(col)] for j in range(rows)]  # inizializzo X come lista 2D
        count_X_position = 0
        for k in y:
            # print("count X = ", count_X_position,"     data2_elem = ",i)
            # print("k ==== ", k)

            X[count_X_position][0] = k
            # print("X[count_X_position][0] = ", X[count_X_position][0])
            count_X_position = count_X_position + 1

        neigh = KNeighborsRegressor(n_neighbors=3, n_jobs=-1)
        # neigh = KNeighborsClassifier(n_neighbors=3, algorithm = 'kd_tree' , weights = 'distance')

        neigh.fit(X, y)

        # predict
        result = []
        for n in dataset_x.outliers:
            result.append(neigh.predict([[n]]))

        result = np.unique(result, axis=0)
        print("len outliers: ", len(dataset_x.outliers), "len result: ", len(result))
        print("result senza duplicati: ", result)
        dataset_x.result = []
        for k in result:
            print("k = ", k[0])
            dataset_x.result.append(k[0])
        if dataset_y is not None:
            dataset_y.result = dataset_x.result

        substituteOutliers(dataset_x, colName)
        # substituteOutliers(dataset_y, colName)
        # dataset_x.data[colName][dataset_x.data[colName] == j] = np.nan

    getNaCount(dataset_x)

    imputer = KNNImputer(n_neighbors=3)
    imputed = imputer.fit_transform(dataset_x.data)
    dataset_x.data = pd.DataFrame(imputed, columns=dataset_x.data.columns)

    return dataset_x.outliers


# calcola gli outliers con il metodo IQR e stampa il boxplot
# input: colonna training set della quale troviamo gli outliers e titolo boxplot
# output: lista outliers per la colonna

def outIQR(train_x, test_x, colName):
    print("\n------ train ------")

    train_x.dataColumn = np.array([])

    for colElement in train_x.data[colName]:
        train_x.dataColumn = np.append(train_x.dataColumn, colElement)

    median = np.median(train_x.dataColumn)
    q3 = np.percentile(train_x.dataColumn, 75)  # upper_quartile
    q1 = np.percentile(train_x.dataColumn, 25)  # lower_quartile
    iqr = q3 - q1

    print("mediana: ", median)
    print("q1: ", q1)
    print("q3: ", q3)
    print("iqr: ", iqr)

    l = q1 - 1.5 * iqr
    r = q3 + 1.5 * iqr
    print("l: ", l, "    r:", r)

    # trovo gli outliers e li inserisco in una lista

    train_x.outliers = []
    count = 0
    for i in train_x.dataColumn:
        if i < l or i > r:
            count = count + 1
            train_x.outliers.append(i)
            print("-- outlier n ", count, ":  ", train_x.outliers[count - 1])

    print("\n------ test ------")
    test_x.dataColumn = np.array([])

    for colElement in train_x.data[colName]:
        test_x.dataColumn = np.append(test_x.dataColumn, colElement)

    test_x.outliers = []
    count = 0
    for j in test_x.dataColumn:
        if j < l or j > r:
            count = count + 1
            test_x.outliers.append(j)
            print("-- outlier n ", count, ":  ", test_x.outliers[count - 1])

    return train_x.outliers


def outIQR3(train_x, test_x, title, colName):
    print("\n------ train ------")

    train_x.dataColumn = np.array([])

    for colElement in train_x.data[colName]:
        train_x.dataColumn = np.append(train_x.dataColumn, colElement)

    median = np.median(train_x.dataColumn)
    q3 = np.percentile(train_x.dataColumn, 75)  # upper_quartile
    q1 = np.percentile(train_x.dataColumn, 25)  # lower_quartile
    iqr = q3 - q1

    print("mediana: ", median)
    print("q1: ", q1)
    print("q3: ", q3)
    print("iqr: ", iqr)

    l = q1 - 1.5 * iqr
    r = q3 + 1.5 * iqr
    print("l: ", l, "    r:", r)

    # trovo gli outliers e li inserisco in una lista

    train_x.outliers = []
    count = 0
    for i in train_x.dataColumn:
        if i < l or i > r:
            count = count + 1
            # train_x.outliers.append(i)
            train_x.data[colName][train_x.data[colName] == i] = np.nan

            print("-- outlier n ", count, ":  ", i)

    print("\n------ test ------")
    test_x.dataColumn = np.array([])

    for colElement in train_x.data[colName]:
        test_x.dataColumn = np.append(test_x.dataColumn, colElement)

    test_x.outliers = []
    count = 0
    for j in test_x.dataColumn:
        if j < l or j > r:
            count = count + 1
            # test_x.outliers.append(j)
            test_x.data[colName][test_x.data[colName] == j] = np.nan

            print("-- outlier n ", count, ":  ", test_x.outliers[count - 1])

    return train_x.outliers


# calcola gli outliers con il metodo ZSCORE
# input: colonna training set della quale troviamo gli outliers
# output: lista outliers per la colonna


def createDataColumn(dataset, colName):
    dataset.dataColumn = np.array([])

    for colElement in dataset.data[colName]:
        dataset.dataColumn = np.append(dataset.dataColumn, colElement)


def outZSCORE(train_x, test_x, colName):
    '''
    calcola gli outliers con il metodo ZSCORE
    :param dataset:
    :param colName:
    :return:
    '''

    # train
    print("\n------ train ------")

    train_x.dataColumn = np.array([])

    for colElement in train_x.data[colName]:
        train_x.dataColumn = np.append(train_x.dataColumn, colElement)

    # print("dataColumn: ", dataset.dataColumn)
    count = 0
    threshold = 3
    mean = np.mean(train_x.dataColumn)
    std = np.std(train_x.dataColumn)
    train_x.outliers = []

    for i in train_x.dataColumn:
        z = (i - mean) / std

        if z > threshold:
            count = count + 1
            train_x.outliers.append(i)
            print("-- outlier n ", count, ":  ", train_x.outliers[count - 1])



    # test

    outliers_test = []

    if test_x is not None:
        print("\n------ test ------")
        test_x.dataColumn = np.array([])

        for colElement in test_x.data[colName]:
            test_x.dataColumn = np.append(test_x.dataColumn, colElement)
        count = 0
        test_x.outliers = []
        for j in test_x.dataColumn:
            # print("j==", j)
            z = (j - mean) / std

            if z > threshold:
                count = count + 1
                test_x.outliers.append(j)
                print("-- outlier n ", count, ":  ", test_x.outliers[count - 1])
        outliers_test = test_x.outliers

    return train_x.outliers, outliers_test, mean, std


def outZSCORE3(train_x, test_x, colName):
    '''
    calcola gli outliers con il metodo ZSCORE
    :param dataset:
    :param colName:
    :return:
    '''

    # train
    print("\n------ train ------")

    train_x.dataColumn = np.array([])

    for colElement in train_x.data[colName]:
        train_x.dataColumn = np.append(train_x.dataColumn, colElement)

    # print("dataColumn: ", dataset.dataColumn)
    count = 0
    threshold = 3
    mean = np.mean(train_x.dataColumn)
    std = np.std(train_x.dataColumn)
    train_x.outliers = []

    for i in train_x.dataColumn:
        z = (i - mean) / std

        if z > threshold:
            count = count + 1
            # train_x.outliers.append(i)
            train_x.data[colName][train_x.data[colName] == i] = np.nan
            print("-- outlier n ", count, ":  ", i)

    print("\n------ test ------")

    # test
    test_x.dataColumn = np.array([])

    for colElement in test_x.data[colName]:
        test_x.dataColumn = np.append(test_x.dataColumn, colElement)

    count = 0
    test_x.outliers = []
    for j in test_x.dataColumn:
        # print("j==", j)
        z = (j - mean) / std

        if z > threshold:
            count = count + 1
            # test_x.outliers.append(j)
            test_x.data[colName][test_x.data[colName] == j] = np.nan
            print("-- outlier n ", count, ":  ", j)

    return train_x.outliers, mean, std


# data la lsita di outliers di una colonna, li sostituisco con il metodo KNN, che avrà come input sia
# il training che il test, poichè devo modificarli entrambi colonna x colonna
def knnDetectionTRAIN(train_x, test_x, colName):
    # copio dataset in lista y e tolgo outliers
    y = train_x.data[colName].copy()
    for i in train_x.outliers:
        # print("i ==== ", i)
        y = y[y != i]

    print("y ==== ", y)
    # ORA ABBIAMO TOLTO E SOSTITUITO OUTLIER : USIAMO KNN !!!!!
    print("len(train_x.outliers) === ", len(train_x.outliers))
    lenX = len(train_x.data[colName]) - len(train_x.outliers)
    print("lenX == ", lenX)
    print("lenY == ", len(y))

    rows = lenX
    col = 1
    X = [[0 for i in range(col)] for j in range(rows)]  # inizializzo X come lista 2D
    count_X_position = 0

    print("X ==== ", X)

    # metto dati nella lista 2D "X"

    # per creare lista 2D "X" per poterla usare in KNN in cui devono andarci tutti i valori di data2 tranne outliers
    # così poi a KNN gli do X senza outlier che gli passo separatamente, in modo da calcolare media dei k vicini e sostituirli
    for k in y:
        # print("count X = ", count_X_position,"     data2_elem = ",i)
        # print("k ==== ", k)

        X[count_X_position][0] = k
        # print("X[count_X_position][0] = ", X[count_X_position][0])
        count_X_position = count_X_position + 1

    print("\n\n--------- KNN TRAIN ------ ")

    # fit
    neigh = KNeighborsRegressor(n_neighbors=3, n_jobs=-1)

    neigh.fit(X, y)

    # predict
    result = []
    for i in train_x.outliers:
        result.append(neigh.predict([[i]]))

    # print("result: ", result[0][0],result[1][0])
    # print("\n\nresult: ", result)

    # poichè nel test set non ho una corrispondenza 1 a 1 tra result e numero di outliers, rimuovo da result
    # i duplicati, poichè avrò un solo result per gli oulliers inferiori e un solo resutl per quelli superiori
    result = np.unique(result, axis=0)
    print("result senza duplicati: ", result)
    appendDict(colName, result[0][0], train_x)
    # train_x.outliersDict[colName] = result
    # outliersDict[colName] = result

    if len(result) > 2:
        print("Lenght result >2")
        return -1

    train_x.result = result
    if test_x is not None:
        test_x.result = result


def knnDetectionTRAIN2(train_x, test_x, colName):
    imputer = KNNImputer(n_neighbors=1)
    # imputer = IterativeImputer(random_state = 42)
    imputed = imputer.fit_transform(train_x.data)
    imputed_test = imputer.transform(test_x.data)
    train_x.data = pd.DataFrame(imputed, columns=train_x.data.columns)
    test_x.data = pd.DataFrame(imputed_test, columns=test_x.data.columns)


def substituteOutliers(dataset, colName, find_method, substitute_method):
    '''
    # result = [[-2.71536111] [ 2.65369323]]
    #   outliers =      2.8855370482008214
    -- outlier n  2 :   2.9115293876047064
    -- outlier n  3 :   3.1141434886609813
    -- outlier n  4 :   -3.1585339273483033
    -- outlier n  5 :   -3.3372981576055034
    -- outlier n  6 :   -3.3824899824206835
    '''
    if substitute_method == "KNN":
        if find_method == "IQR":
            if len(dataset.result) == 1:
                for i in dataset.outliers:
                    dataset.data[colName][dataset.data[colName] == i] = (dataset.result[0][0])
            # sostuituiamo i risultati con gli outliers nel dataset originario
            if len(dataset.result) > 1:
                for i in dataset.outliers:
                    res = checkClosestOutlier(i, dataset.result)
                    dataset.data[colName][dataset.data[colName] == i] = (res)

        if find_method == "ZSCORE" or find_method == "DBSCAN":
            if len(dataset.result) == 1:
                for i in dataset.outliers:
                    dataset.data[colName][dataset.data[colName] == i] = (dataset.result[0][0])
            if len(dataset.result) > 1:
                for i in dataset.outliers:
                    res = checkClosestOutlier2(i, dataset.result)
                    dataset.data[colName][dataset.data[colName] == i] = (res)

        if find_method == "ZSCORE2":
            if len(dataset.result) == 1:
                for i in dataset.outliers:
                    dataset.data[colName][dataset.data[colName] == i] = (dataset.result[0][0])
            if len(dataset.result) == 2:
                for i in dataset.outliers:
                    res = checkClosestOutlier(i, dataset.result)
                    dataset.data[colName][dataset.data[colName] == i] = (res)

    if substitute_method == "MEAN":
        for i in dataset.outliers:
            dataset.data[colName][dataset.data[colName] == i] = dataset.result

    # checkOutliersAfterKNN(dataset,colName)


def checkClosestOutlier(outlier, resultList):
    '''
    resultList[0][0] = -2.71536111
    resultList[1][0] = 2.65369323
    outlier n  1 :    2.8855370482008214
    outlier n  6 :   -3.3824899824206835

    diff1 e diff2 sono le distanze in valore assoluto dall'outlier a entrambi i valori di resultList

    Nel caso di outlier n 1 bisogna sostituirlo con resultList[1][0], che è il valore più vicino
    quindi calcolo la distanza dell'outlier dai due valori contenuti in resulList,
    e prendo la distanza minore (valore assoluto)
    '''

    diff1 = abs(outlier - resultList[0][0])
    diff2 = abs(outlier - resultList[1][0])
    # print("diff1 : ", diff1, "  diff2: ",diff2)

    if diff2 < diff1:
        return diff2
    else:
        return diff1


def checkClosestOutlier2(outlier, resultList):
    resultList = np.asarray(resultList)
    idx = (np.abs(resultList - outlier)).argmin()
    return resultList[idx]


def checkOutliersAfterReplacement(train_x, test_x, colName, find_method):
    if find_method == "IQR":
        # CALCOLO OUTLIERS DEL TRAINING SET FINALE DELLA SIGNOLA FEATURE
        title = colName + "after KNN"
        outliers = outIQR(train_x, title, colName)

    if find_method == "ZSCORE":
        returnZ = outZSCORE(train_x, test_x, colName)
        outliers_train = returnZ[0]
        outliers_test = returnZ[1]

    if len(outliers_train) == 0:
        print(colName, ": Tutti gli outliers nel training set sono stati sostituiti\n\n")
        return 0
    if len(outliers_test) == 0:
        print(colName, ": Tutti gli outliers nel test set sono stati sostituiti\n\n")
        return 0


def changeColNames(dfDataset):
    # print("TOTALE PRIMA-   ", df_imputed)
    # print("COLONNA 0-   ", df_imputed[0])

    string = "F"
    for i in range(1, 21):
        currColumn = string + str(i)
        index = i - 1
        # print("index: ", index)
        # print(df_imputed.rename(columns={index: 'F1'}))
        dfDataset.rename(columns={index: currColumn}, inplace=True)

    print("TOTALE DOPO-      ", dfDataset)


# sostuisce NaN con media per ogni colonna
def naMean2(train_x, test_x):
    getNaCount(train_x)
    print("train x na count : ", train_x.naCount)
    if test_x is not None:
        getNaCount(test_x)
        print("test x na count : ", test_x.naCount)

    # print(train_dataset['F1'].mean())

    print("\n\nMEDIA PER OGNI ATTRIBUTO: ")

    string = "F"
    for i in range(1, 21):
        currColumn = string + str(i)
        currMean = train_x.data[currColumn].mean()

        print(currColumn, ": ", currMean)
        appendDict(currColumn, currMean, train_x)
        # naDict[currColumn] = currMean
        # train_x.outliersDict[currColumn] = currMean

        train_x.data[currColumn] = train_x.data[currColumn].fillna(currMean)
        if test_x is not None:
            test_x.data[currColumn] = test_x.data[currColumn].fillna(currMean)

    # controlliamo nuovamente che train e test siano senza n/a
    getNaCount(train_x)
    print("train x na count : ", train_x.naCount)
    if test_x is not None:
        getNaCount(test_x)
        print("test x na count : ", test_x.naCount)


def appendDict(key, value, train_x):
    if key in train_x.outliersDict:
        # append the new number to the existing array at this slot
        train_x.outliersDict[key].append(value)
    else:
        # create a new array in this slot
        train_x.outliersDict[key] = [value]




# sostuisce NaN con media per ogni colonna
def naMean(train_x, test_x):
    getNaCount(train_x)
    print("train x na count : ", train_x.naCount)
    getNaCount(test_x)
    print("test x na count : ", test_x.naCount)

    # print(train_dataset['F1'].mean())

    print("\n\nMEDIA PER OGNI ATTRIBUTO: ")

    string = "F"
    for i in range(1, 21):
        currColumn = string + str(i)
        currMean = train_x.data[currColumn].mean()

        print(currColumn, ": ", currMean)
        appendDict(currColumn, currMean, train_x)

        train_x.data[currColumn] = train_x.data[currColumn].fillna(currMean)
        test_x.data[currColumn] = test_x.data[currColumn].fillna(currMean)

    # controlliamo nuovamente che train e test siano senza n/a
    getNaCount(train_x)
    print("train x na count : ", train_x.naCount)
    getNaCount(test_x)
    print("test x na count : ", test_x.naCount)


def naKNN(train_x, test_x):
    getNaCount(train_x)
    imputer = KNNImputer(n_neighbors=3)

    imputed_train = imputer.fit_transform(train_x.data)
    train_x.data = pd.DataFrame(imputed_train, columns=train_x.data.columns)
    save_object(imputer, 'imputer.pkl')

    if test_x is not None:
        imputed_test = imputer.transform(test_x.data)
        test_x.data = pd.DataFrame(imputed_test, columns=test_x.data.columns)


def getNaCount(dataset):
    # per ogni elemento (i,j) del dataset, isna() restituisce
    # TRUE/FALSE se il valore corrispondente è mancante/presente
    boolean_mask = dataset.data.isna()
    # contiamo il numero di TRUE per ogni attributo sul dataset
    count = boolean_mask.sum(axis=0)
    print("count NaN: ", count)
    dataset.naCount = count
    # print(boolean_mask.any())
    return count


def chooseMethods():
    na_methods = ["MEAN", "KNN"]
    find_methods = ["IQR", "ZSCORE"]
    substitute_methods = ["KNN", "MEAN"]
    scale_types = ["STANDARD", "MINMAX", "MAX_ABS", "ROBUST"]
    classifiers = ["MLP", "KNeighbors", "SVC", "DecisionTree", "RandomForest", "QuadraticDiscriminantAnalysis"]

    print("\n\nInserisci i metodi con cui si vuole effettuare la classificazione:\n"
          "na_method: metodo con cui si desiderano sostituire i valori mancanti nel dataset"
          "find_method: metodo con cui si desiderano individuare gli outliers\n"
          "substitute_method: metodo con cui si desiderano sostituire gli outliers\n"
          "scale_type: tipo di scaler che si desidera\n"
          "resampling_method: metodo con cui si vuole effettuare il resampling\n"
          "classifier: classificatore che si vuole utilizzare\n"
          "\n\n")

    print("Scegliere e inserire una tra le seguenti stringhe: MEAN / KNN\nna_method: ")
    na_method = input()
    while na_method not in na_methods:
        print("ATTENZIONE: Inserire una tra le stringhe a disposizione, facendo attenzione a maiuscole e minuscole!")
        print("na_method:")
        na_method = input()

    print("\nScegliere e inserire una tra le seguenti stringhe: IQR / ZSCORE\nfind_method: ")
    find_method = input()
    while find_method not in find_methods:
        print("ATTENZIONE: Inserire una tra le stringhe a disposizione, facendo attenzione a maiuscole e minuscole!")
        print("find_method:")
        find_method = input()

    print("\nScegliere e inserire una tra le seguenti stringhe: KNN / MEAN\nsubstitute_method: ")
    substitute_method = input()
    while substitute_method not in substitute_methods:
        print("ATTENZIONE: Inserire una tra le stringhe a disposizione, facendo attenzione a maiuscole e minuscole!")
        print("substitute_method:")
        substitute_method = input()

    print("\nScegliere e inserire una tra le seguenti stringhe: STANDARD / MINMAX / MAX_ABS / ROBUST\nscale_type: ")
    scale_type = input()
    while scale_type not in scale_types:
        print("ATTENZIONE: Inserire una tra le stringhe a disposizione, facendo attenzione a maiuscole e minuscole!")
        print("scale_type:")
        scale_type = input()

    print(
        "\nScegliere e inserire una tra le seguenti stringhe: MLP / KNeighbors / SVC / DecisionTree / RandomForest / QuadraticDiscriminantAnalysis\nclassifier: ")
    classifier = input()
    while classifier not in classifiers:
        print("ATTENZIONE: Inserire una tra le stringhe a disposizione, facendo attenzione a maiuscole e minuscole!")
        print("classifier:")
        classifier = input()

    return na_method, find_method, substitute_method, scale_type, classifier

def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def main():
    datasetPath = './training_set.csv'
    dataset = pd.read_csv(datasetPath)

    train_x = Dataset("train_x", None)
    test_x = Dataset("test_x", None)

    train_y = Dataset("train_y", None)
    test_y = Dataset("test_y", None)

    # separiamo le features x dal target y
    x = dataset.iloc[:, 0:20].values
    y = dataset.iloc[:, 20].values

    na_method, find_method, substitute_method, scale_type, classifier = chooseMethods()
    print(na_method, find_method, substitute_method, scale_type, classifier)
    ''' 
        
          "resampling_method --> ????? \n"
    '''

    preProcessing(train_x, test_x, train_y, test_y, x, y, na_method, find_method, substitute_method, scale_type)
    print(find_method, "---", substitute_method, "---", scale_type, "--- ALLKNN", classifier)

    crossValidation.cross(train_x, test_x, train_y, test_y, classifier)

    print("dict === ", train_x.outliersDict)
    # suono quando finisce
    duration = 400  # milliseconds
    freq = 440  # Hz
    winsound.Beep(freq, duration)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
