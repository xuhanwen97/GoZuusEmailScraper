import requests
from lxml import html
import csv
import os

# Follows this tutorial with modifications for gozuus: http://kazuar.github.io/scraping-tutorial/


# Performs a login request and returns the created session after logging in
def sendLoginRequest():
    from getpass import getpass

    email = input('Enter your Gozuus email: ')
    password = getpass("Enter your Gozuus password")

    payload = {
        "email": email,
        "password": password,
        "commit": "Login",
        # As I understand, some websites need this auth-token style key to allow you to login
        # "authenticity_token": "<authenticity_token>",
    }

    session_requests = requests.session()

    login_url = "https://login.gozuus.com/"
    result = session_requests.get(login_url)

    tree = html.fromstring(result.text)

    # Unsure why I need this, was following a tutorial
    authenticity_token = list(set(tree.xpath("//input[@name='authenticity_token']/@value")))[0]

    result = session_requests.post(
        login_url,
        data=payload,
        headers=dict(referer=login_url)
    )

    # TODO: Check if login succeeds - idk how

    return session_requests


# Takes in the login_session returned by the login request, and returns a list of email list names
def getAllEmailLists(login_session):

    url = 'http://gtdeltachi.gozuus.com/lists'
    result = login_session.get(
        url,
        headers=dict(referer=url)
    )

    tree = html.fromstring(result.content)

    # Gets all the email list elements
    email_list_names = tree.xpath("//span[@class='subscribers']/a")

    return email_list_names


def getEmailListSubscribers(login_session, email_list_path):
    url = base_url + email_list_path
    result = login_session.get(
        url,
        headers=dict(referer=url)
    )

    tree = html.fromstring(result.content)

    # Gets the name of the email list
    email_list_name = tree.xpath("//div[@id='left_column']//h1/text()")[0].split("@")[0]

    print("Parsing email-list: {}".format(email_list_name))

    # Gets all divs for users that have a check box next to them
    # checked_users_divs = tree.xpath("//input[@checked='checked']/parent::*")

    # Gets all the names for the users that have a checkbox next to their name
    checked_users = tree.xpath("//input[@checked='checked']/parent::*//label/text()")

    # This line gets all the emails for users that have a checkbox next to their name
    checked_users_emails = tree.xpath("//input[@checked='checked']/parent::*//span[@class='tag']/text()")

    email_list_subscribers = []
    for i in range(0, len(checked_users)):
        subscriber = {
            "name": checked_users[i],
            "email": checked_users_emails[i][1:-1]
        }
        email_list_subscribers.append(subscriber)

    return email_list_name, email_list_subscribers


def parseAllLists():

    login_session = sendLoginRequest()

    email_list_names = getAllEmailLists(login_session)

    for email_list in email_list_names:

        # Make the get request to the specific list's url
        email_list_path = email_list.attrib['href']
        email_list_name, email_list_subscribers = getEmailListSubscribers(login_session, email_list_path)

        filename = "{}/{}_list.csv".format(dirName, email_list_name)

        try:
            os.remove(filename)
        except OSError:
            pass

        with open(filename, 'w') as output_file:
            keys = email_list_subscribers[0].keys()
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(email_list_subscribers)


def makeOutputDirectory(dirName):
    try:
        # Create target Directory
        os.mkdir(dirName)
        print("Directory ", dirName, " Created ")
    except FileExistsError:
        print("Directory ", dirName, " already exists")


if __name__ == '__main__':
    base_url = "http://gtdeltachi.gozuus.com"

    print("Start parsing email lists\n\n")

    dirName = "email_list_subs_csv_out"
    makeOutputDirectory(dirName)

    parseAllLists()

    print("Finishing parsing email lists\n\n")

