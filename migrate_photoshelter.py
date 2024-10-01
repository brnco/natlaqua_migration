'''
migrates still image data from photoshelter
'''
import os
import pathlib
import requests
import http.client

conn = http.client.HTTPSConnection("www.photoshelter.com")

conn.request("GET", "/psapi/v4.0//library")

response = conn.getresponse()

data = response.read()

print(data.decode("utf-8"))
