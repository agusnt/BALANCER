#/usr/bin/python3
"""
Class to manage a rolling average

Requirements: numpy library

@AUTHOR: Navarro Torres, Agustín
@DATE: 13/12/2020
@EMAIL: agusnt (at) unizar (dot) es
@UPDATES:
"""
from numpy import mean

class RollingAVG:
    ###########################################################################
    # Class attribute
    ###########################################################################
    _list = None
    _max = None

    ###########################################################################
    # Not override functions
    ###########################################################################
    def __init__(self, maxx):
        self._max = maxx
        self._list = []

    ###########################################################################
    # API functions
    ###########################################################################
    def add(self, elem):
        """
        Add a new element to the list

        Parameters:
            - elem : new element to add
        """
        if len(self._list) >= self._max:
            self._list.pop(0)
        self._list.append(elem)

    def avg(self):
        """
        Return the average of the numbers
        """
        return mean(self._list)
    
    def nElements(self):
        """
        Return the current number of elements of the list
        """
        return len(self._list)

    def max(self):
        """
        Return elements to calculate the rolling average
        """
        return self._max
