import pytesseract
import shutil
import os
import re

try:
    from PIL import Image
except ImportError:
    import Image
import cv2
import numpy as np
from matplotlib import pyplot as plt


class ImageStringToDate():

    def __init__(self, img, img_name="No Image Name"):
        """Requires an image file that has been already read.
        Attept to read the image using pytesseract image_to_string method using multiple different thresholds from the cv2 library
        and find days, dates, months, and years within the string collected by the image_to_string method."""
        self.img_name = img_name
        self.img = img

        ret, thresh1 = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
        ret, thresh2 = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
        ret, thresh3 = cv2.threshold(img, 127, 255, cv2.THRESH_TRUNC)
        ret, thresh4 = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO)
        ret, thresh5 = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO_INV)

        # titles for different thresholding
        self.titles = ['Original Image', 'BINARY/thresh1', 'BINARY_INV/thresh2', 'TRUNC/thresh3', 'TOZERO/thresh4',
                       'TOZERO_INV/thresh5']
        self.images = [img, thresh1, thresh2, thresh3, thresh4, thresh5]

        # image to string
        self.original = pytesseract.image_to_string(img)
        self.thresh1 = pytesseract.image_to_string(thresh1)
        self.thresh2 = pytesseract.image_to_string(thresh2)
        self.thresh3 = pytesseract.image_to_string(thresh3)
        self.thresh4 = pytesseract.image_to_string(thresh4)
        self.thresh5 = pytesseract.image_to_string(thresh5)
        self.all_thresh = [self.original, self.thresh1, self.thresh2, self.thresh3, self.thresh4, self.thresh5]

        # possible dates in different formats
        self.possibleDays = []
        self.possibleDates = []
        self.possibleMonths = []
        self.possibleYears = []

        # initialize and find all possibilities
        lowerAllText = self.return_one_string()
        lowerAllTextLines = lowerAllText.split("\n")

        for line in lowerAllTextLines:
            self.find_day(line)
            self.find_month(line)
            self.find_only_year(line)
            self.find_date(line)

    def print_all_thresh(self):

        print(self.img_name + ":")
        for types in range(6):
            print("__________")
            print(self.titles[types] + ":")
            try:
                cv2_imshow(self.images[types])
            except:
                print("cannot show image")
            print(self.all_thresh[types])
            print("-----")

    def return_one_string(self):
        """returns one string for all thresholds in lower case"""

        one_string = ""
        for i in range(6):
            one_string += self.all_thresh[i].lower()
        return one_string

    def imshow(self, threshNum):
        '''return picture of the thresholding
        thresh refers to type of thresholding within cv2 library
        0: original
        1: binary
        2: binary inv
        3: trunc
        4: tozero
        5: tozero inv'''
        # cv2.namedWindow(self.img_name + " threshold " +str(threshNum), cv2.WINDOW_NORMAL)
        plt.imshow(self.images[threshNum], 'gray')
        plt.show()

    def imshow_all(self):

        for i in range(6):
            plt.subplot(2, 3, i + 1), plt.imshow(self.images[i], 'gray')
            plt.title(self.titles[i])
            plt.xticks([]), plt.yticks([])

        plt.show()

    def find_day(self, line):
        """Attempt to find day based on common day of the week words or phrases"""

        DAYS_PATTERN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                        "mon", "tue", "tues", "wed", "thur", "thurs", "fri", "sat",
                        "sun"]  # may need to expand later to include more languages

        for day in DAYS_PATTERN:
            if day in line:
                if day not in self.possibleDays:
                    self.possibleDays.append(day)

        return self.possibleDays

    def find_month(self, line):
        """Attempt to find month based on common month words or phrases
        Additionally check and attempt to find corresponding date or year based on number of digits in a row"""

        MONTHS_PATTERN = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
                          'october', 'november',
                          'december', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct',
                          'nov', 'dec']

        for month in MONTHS_PATTERN:
            if month in line:
                if month not in self.possibleMonths:
                    self.possibleMonths.append(month)

                # find date that cooresponds with month
                numsOnlyLine = re.sub(r"\D", " ", line)  # remove all characters except digits
                lineSplit = numsOnlyLine.split(" ")  # split by space to make it into a list
                for char in lineSplit:

                    # look at each character in the split line to detect date or year
                    if char.isdigit() and len(char) <= 3:
                        if char not in self.possibleDates:
                            self.possibleDates.append(char)
                    elif char.isdigit() and len(char) == 4:
                        if char not in self.possibleYears:
                            self.possibleYears.append(char)

        return self.possibleMonths

    def find_only_year(self, line):
        """Attempt to find year based on 4 digit pattern for year"""

        onlyDigits = re.sub(r"\D", " ", line)
        onlyDigitsList = onlyDigits.split(" ")
        for num in onlyDigitsList:
            if len(num) == 4:
                if num not in self.possibleYears:
                    self.possibleYears.append(num)

        return self.possibleYears

    def find_date(self, line):
        """Attempt to find full date based on number of digits in seperate numbers as well as conventions
        Default American dates"""

        onlyDigits = re.sub(r"\D", " ", line)
        onlyDigitsList = onlyDigits.split(" ")

        # check if all digits and not just blanks
        flag = True
        for num in onlyDigitsList:

            if not num.isdigit():
                flag = False

        if len(onlyDigitsList) == 3 and flag:  # only if 3 different numbers for date month and year

            if int(onlyDigitsList[
                       0]) > 12:  # if first number is greater than 12, then the first number must be a date; fastest way to check if not US date/month

                month = str(onlyDigitsList[1])
                date = str(onlyDigitsList[0])
                year = str(onlyDigitsList[2])
                if month not in self.possibleMonths:
                    self.possibleMonths.append(month)
                if date not in self.possibleDates:
                    self.possibleDates.append(date)
                if year not in self.possibleYears:
                    self.possibleYears.append(year)

            else:
                month = str(onlyDigitsList[0])
                date = str(onlyDigitsList[1])
                year = str(onlyDigitsList[2])
                if month not in self.possibleMonths:
                    self.possibleMonths.append(month)
                if date not in self.possibleDates:
                    self.possibleDates.append(date)
                if year not in self.possibleYears:
                    self.possibleYears.append(year)

        try:
            return {"month": month, "date": date, "year": year}
        except:
            return None

    def extract_possible_date(self):
        """Return dictionary containing possible Dates inside lists"""

        day = self.possibleDays
        date = self.possibleDates
        month = self.possibleMonths
        year = self.possibleYears

        dateDic = {"day": day, "date": date, "month": month, "year": year}

        return dateDic


# obtain directory path
path = os.path.dirname(os.path.abspath(__file__))
print(path + "\\flyers\\")

# obtain path for flyers and individual images
flyerDir = path + "\\flyers\\"
imgList = os.listdir(flyerDir)

print(imgList)

imgStringList = []
for img in imgList:
  imgStringList.append(ImageStringToDate(cv2.imread(flyerDir+img, 0), img))
  print("loaded: " + img)


#imgStringList[0].extract_possible_date()
for img in imgStringList:
  print(img.img_name)
  #img.imshow_all()
  print(img.extract_possible_date())
  print("__________")