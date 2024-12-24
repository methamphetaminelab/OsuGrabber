import os
import sys
import asyncio
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

logger.remove()
logger.add(sys.stderr, format="[<level>{level}</level>] {message}", level="INFO", colorize=True)

cookieValue = "COOKIE_VALUE"

async def installDriver():
    try:
        global driver
        global downloadFolder
        logger.info("Installing ChromeDriver")
        chromedriver_autoinstaller.install()

        downloadFolder = os.path.join(os.getcwd(), "maps")
        if not os.path.exists(downloadFolder):
            os.makedirs(downloadFolder)

        options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": downloadFolder}
        options.add_experimental_option("prefs", prefs)

        options.add_argument("--headless") # можно закомментировать, чтобы видеть браузер

        options.add_argument("--disable-gpu")=
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)

        logger.success("ChromeDriver installed")

        logger.info("Opening browser")
        driver.get("https://osu.ppy.sh/community/chat?channel_id=32359962")
        logger.success("Browser opened")

        logger.info("Importing cookies")
        cookies = [
            {
                "name": "osu_session",
                "value": f"{cookieValue}",
                "domain": ".ppy.sh",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "Lax",
            }
        ]

        for cookie in cookies:
            driver.add_cookie(cookie)

        driver.get("https://osu.ppy.sh/community/chat?channel_id=32359962")
        logger.success("Cookies imported")
    except Exception as e:
        logger.error(f"Error in installDriver: {e}")

async def getExistingLinks():
    try:
        global driver
        logger.info("Getting existing links")
        chatMessages = driver.find_elements(By.CLASS_NAME, "chat-message-item__entry")
        
        existingLinks = []
        for message in chatMessages:
            try:
                link = message.find_element(By.TAG_NAME, "a").get_attribute("href")
                if link:
                    existingLinks.append(link)
            except Exception:
                continue

        logger.info(f"Found {len(existingLinks)} links")
        return existingLinks
    except Exception as e:
        logger.error(f"Error in getExistingLinks: {e}")
        return []
    
async def sendMessage():
    try:
        global driver
        logger.info("Sending message")
        chatInput = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "chat-input__box")))
        chatInput.send_keys("!r")
        chatInput.send_keys(Keys.RETURN)
        logger.success("Message sent")

        existingLinks = []
        while not existingLinks:
            existingLinks = await getExistingLinks()

        logger.info(f"Map link: {existingLinks[-1]}")

        return existingLinks[-1]

    except Exception as e:
        logger.error(f"Error in sendMessage: {e}")

async def downloadMap(link):
    try:
        global driver
        if not link:
            logger.error("Invalid link")
            return
        logger.info(f"Downloading map: {link}")
        
        driver.execute_script("window.open(arguments[0], '_blank');", link)
        
        driver.switch_to.window(driver.window_handles[-1])
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='btn-osu-big btn-osu-big--beatmapset-header ']"))).click()
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        logger.error(f"Error in downloadMap: {e}")

async def installMaps():
    try:
        global downloadFolder
        logger.info("Installing maps")

        maps = os.listdir(downloadFolder)

        for map in maps:
            mapPath = os.path.join(downloadFolder, map)

            if mapPath.endswith(".crdownload") or mapPath.endswith(".tmp"):
                logger.info(f"Waiting for map: {map}")

                while mapPath.endswith(".crdownload") or mapPath.endswith(".tmp"):
                    
                    await asyncio.sleep(0.1)

                    maps = os.listdir(downloadFolder)
                    for map in maps:
                        mapPath = os.path.join(downloadFolder, map)
                        if mapPath.endswith(".crdownload") or mapPath.endswith(".tmp"):
                            break
                    else:
                        break

            if mapPath.endswith(".osz"):
                logger.info(f"Installing map: {map}")
                os.startfile(mapPath)
                logger.success(f"Map installed: {map}")
            else:
                logger.warning(f"Map file not valid for installation: {map}")

    except Exception as e:
        logger.error(f"Error in installMaps: {e}")

async def main():
    count = int(input("Number of maps: "))

    for _ in range(count):
        link = await sendMessage()
        download_task = asyncio.create_task(downloadMap(link))
        await asyncio.sleep(1)
        install_task = asyncio.create_task(installMaps())

        await download_task
        await install_task

        await asyncio.sleep(1)

    logger.success("All maps installed")

    driver.get("https://osu.ppy.sh/community/chat?channel_id=32359962")

if __name__ == "__main__":
    if cookieValue == "COOKIE_VALUE":
        logger.error("Cookie value not set")
        sys.exit(1)
    asyncio.run(installDriver())
    asyncio.run(main())
