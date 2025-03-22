# Text analyzer
A Python application for analyzing handwritten text in Russian.

The simple interface allows you to paste text from the clipboard. After the analysis, statistics of repeated words and other indicators are displayed:
- number of characters,
- readability index,
- nebula index,
- water,
- turbidity.

![alt text](https://raw.githubusercontent.com/be-in/text-analyzer/main/interface.jpg)

For this code to work, you will need python itself and the nltk library.
To install it, you will need to run this command on the command line:

> pip install nltk

In the code itself (text_analyzer.py) attempts are being made to download certain NLTK resources (punkt, punkt_tab, stopwords). If these resources are not found, the code tries to download them. Therefore, after installing nltk, it is highly advisable to run the code and wait for the necessary data to be downloaded before attempting to use the program in full. This will prevent LookupError errors during execution.

Оr you can find a similar online service that will be limited in free use, requires a mandatory Internet connection and a fee for its use. :)
