from __future__ import absolute_import, division, print_function
import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from lsst.utils import getPackageDir
from .phosim_cpu_pred import CpuPred 


__all__ = ['OpSimOrdering']

class OpSimOrdering(object):
    """
    Code to split the Twinkles 3 obsHistIDs into sets that will be ordered so
    that we would try to do Twinkles_3p1 first, followed by Twinkles_3p2,
    followed by Twinkles_3p3
    Parameters
    ----------
    opSimDBPath : absolute path to OpSim database
    timeMax : float, unit of hours, default to 0.9
        a threshold of time, such that any OpSim pointings with predictedPhoSim
        times above that threshold will be dropped.

    Attributes
    ----------
    distinctGroup : list
        unique combination of variables in which the records are grouped. The
        variables are 'night' and 'filter'
    timeMax : float,
        max value of `predictedPhoSimTimes` in hours for a record for it to be
        used in the calculation
    filteredOpSim : `pd.DataFrame`
        dataFrame representing the OpSim data with duplicate records dropped in
        favor of the ones with propID ==54 (WFD) and any record that has a
        `predictedPhoSimTimes` > `self.timeMax` dropped
    """
    def __init__(self, opSimDBPath,
                 randomForestPickle=None,
                 timeMax=120.0,
                 ignorePredictedTimes=False,
                 minimizeBy='predictedPhoSimTimes'):
        """
        Parameters
        ----------
        opSimDBPath : string, mandatory
            absolute path to a sqlite OpSim database
        randomForestPickle : string, defaults to None
            absolute path to a pickle of an instance of
            `sklearn.ensemble.forest.RandomForestRegressor`
        timeMax: float, defaults to 120.0
            max value of predicted PhoSim Run times of selected OpSim records.
            Records with predicted PhoSIm run times beyond this value are
            filtered out of `filteredOpSim`
        """
        twinklesDir = getPackageDir('Twinkles')

        self.ignorePredictedTimes = ignorePredictedTimes
        self._opsimDF = self.fullOpSimDF(opSimDBPath)
        self._opsimDF['year'] = self._opsimDF.night // 365

        if randomForestPickle is None:
            randomForestPickle = os.path.join(twinklesDir, 'data',
                                              'RF_pickle.p')

        if self.ignorePredictedTimes:
            if minimizeBy not in self._opsimDF.columns:
                raise NotImplementedError('minimizing by {} not implemented, try `expMJD`' minimizeBy)
            self.minimizeBy = minimizeBy
        else:
            if not os.path.exists(randomForestPickle):
                raise ValueError('pickle does not exist at {}'.format(randomForestPickle))

            self.cpuPred = CpuPred(rf_pickle_file=randomForestPickle,
                                   opsim_df=self._opsimDF,
                                   fieldID=1427)
            self._opsimDF['predictedPhoSimTimes'] = self.predictedTimes()

        self.timeMax = timeMax 
        self.distinctGroup = ['night', 'filter']

    def predictedTimes(self, obsHistIDs=None):
        """
        predicted time for `PhoSim` image sigmulation on a SLAC 'fell' CPU
        in units of hours 

        Parameters
        ----------
        obsHistIDs : float or sequence of integers, defaults to None
            if None, obsHistIDs defaults to the sequence of obsHistIDs in
            `self._opsimDF`
        Returns
        -------
        `numpy.ndarray` of predicted PhoSim simulation times in hours
        """
        # default obsHistIDs
        if obsHistIDs is None:
            obsHistIDs = self._opsimDF.reset_index()['obsHistID'].values

        obsHistIds = np.ravel(obsHistIDs)
        times = np.ones_like(obsHistIds) * np.nan 
        for i, obshistid in enumerate(obsHistIds):
            times[i] = self.cpuPred(obshistid)

        # convert to hours from seconds before return
        return times / 3600.0

    @property
    def uniqueOpSimRecords(self):
        """
        - drop duplicates in favor of propID for WFD
        """
        pts = self._opsimDF.copy()
        # Since the original SQL query ordered by propID, keep=first 
        # preferentially chooses the propID for WFD
        pts.drop_duplicates(subset='obsHistID', inplace=True, keep='first')
        return pts

    @property
    def filteredOpSim(self):
        """
        - drop records where the phoSim Runtime estimate exceeds threshold
        """
        thresh = self.timeMax
        if self.ignorePredictedTimes:
            return self.uniqueOpSimRecords
        else:
            return self.uniqueOpSimRecords.query('predictedPhoSimTimes < @thresh')

    @property
    def obsHistIDsPredictedToTakeTooLong(self):
        """
        obsHistIDs dropped from Twink_3p1, Twink_3p2, Twink_3p3 because the
        estimated phoSim run time is too long in the form a dataframe with
        column headers `obsHistID` and `predictedPhoSimTimes`.

        This returns None, if no obsHistIds are missing due to their
        predictedPhoSimRunTime being too long
        """
        if self.ignorePredictedTimes:
            return None
        filteredObsHistID = \
            tuple(self.filteredOpSim.reset_index().obsHistID.values.tolist())

        missing = self.uniqueOpSimRecords.query('obsHistID not in @filteredObsHistID')
        if len(missing) > 0:
            return missing[['obsHistID', 'predictedPhoSimTimes']]
        else:
            return None

    @property
    def Twinkles_WFD(self):
        """
        return a dataframe with all the visits for each unique combination with
        the lowest propID (all WFD visits or all DDF visits) in each unique
        combination
        """
        groupDistinct = self.filteredOpSim.groupby(self.distinctGroup)
        SelectedObsHistIDs = groupDistinct.propID.transform(min) == self.filteredOpSim.propID
        return self.filteredOpSim[SelectedObsHistIDs]
     
    @property
    def Twinkles_3p1(self):
        """
        For visits selected in Twinkles_WFD, pick the visit in each unique
        combination with the lowest value of the `predictedPhoSimTimes`
        """
        grouped = self.Twinkles_WFD.groupby(self.distinctGroup)
        idx  = grouped[self.minimizeBy]transform(min) == \
            self.Twinkles_WFD[self.minimizeBy]
        return self.Twinkles_WFD[idx].sort_values(by='expMJD', inplace=False)
    
    @property
    def Twinkles_3p2(self):
        """
        dr5 Observations that are in `filteredOpSim` and have not been done in 
        Twinkles_3p1
        """
        doneObsHist = tuple(self.Twinkles_3p1.obsHistID.values.tolist())
        return self.filteredOpSim.query('year == 4 and obsHistID not in @doneObsHist').sort_values(by='expMJD',
                                                                                                   inplace=False)
    @property
    def Twinkles_3p3(self):
        obs_1 = self.Twinkles_3p1.obsHistID.values.tolist()
        obs_2 = self.Twinkles_3p2.obsHistID.values.tolist()
        obs = tuple(obs_1 + obs_2)
        return self.filteredOpSim.query('obsHistID not in @obs').sort_values(by='expMJD', inplace=False)
        
    @staticmethod
    def fullOpSimDF(opsimdbpath, query="SELECT * FROM Summary WHERE FieldID == 1427 ORDER BY PROPID"):
        engine = create_engine('sqlite:///' + opsimdbpath)
        pts = pd.read_sql_query(query, engine)
        return pts