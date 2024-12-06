import time
import requests
from tqdm import tqdm
from loguru import logger


class ITManage:
    def __init__(self, username, password, courseName):
        self.point_name = None
        self.preview_courseId = None
        self.courseId = None
        self.courseName = courseName
        self.username = username
        self.password = password
        self.host = "https://stu.ityxb.com"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://stu.ityxb.com",
            "Referer": "https://stu.ityxb.com/",
        }
        self.cookie = None

    @staticmethod
    def getTimestamp():
        return str(int(time.time() * 1000))

    @staticmethod
    def generate_point(num):
        result = []
        for i in range(0, num + 1, 5):  # 以步长为5进行循环
            if i == 0:
                result.append(1)
            else:
                result.append(i)
        result.append(num)
        return result

    def login(self, ):
        payload = {
            "automaticLogon": "false",
            "username": self.username,
            "password": self.password,
        }

        # 发起 POST 请求
        response = requests.post(self.host + "/back/bxg_anon/login", headers=self.headers, data=payload)

        # 检查响应状态
        if response.status_code == 200:
            logger.debug(f"登录成功,当前课程:《{self.courseName}》")
            self.cookie = response.cookies
        else:
            logger.error(f"登录失败，状态码: {response.status_code}")

    def get_login_info(self, ):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://stu.ityxb.com/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }

        # 使用前一个函数返回的 cookies 发起 GET 请求
        response = requests.get(self.host + "/back/bxg_anon/user/loginInfo?t=" + self.getTimestamp(),
                                headers=self.headers, cookies=self.cookie)

        # 检查响应状态
        if response.status_code == 200:
            response_json = response.json()
            logger.info("欢迎您: " + response_json['resultObject']['name'])
            # logger.debug(response_json['resultObject']['classInfoVo'])
            return response.json()  # 返回 JSON 数据
        else:
            logger.error(f"请求失败，状态码: {response.status_code}")
            return None

    def get_courses(self):
        # 设置课程列表的请求数据
        payload = {
            "type": 1,
            "pageNumber": 1,
            "pageSize": 100,
        }

        # 发送 POST 请求以获取课程列表
        response = requests.post(self.host + "/back/bxg/course/getHaveList", headers=self.headers,
                                 cookies=self.cookie, data=payload)

        # 检查响应状态
        if response.status_code == 200:
            logger.debug("课程列表获取成功")
            response_json = response.json()
            for i in response_json['resultObject']['items']:
                if i['name'] == "Java程序设计任务驱动教程":
                    self.courseId = i['id']
            return response_json
        else:
            logger.error(f"课程列表获取失败，状态码: {response.status_code}")
            return None

    def get_preview_list(self,):
        # 获取预习列表的请求 URL 和参数
        url = f"{self.host}/back/bxg/preview/list?name=&isEnd=&pageNumber=1&pageSize=10&type=1&courseId={self.courseId}&t={self.getTimestamp()}"

        # 发送 GET 请求以获取预习列表
        response = requests.get(url, headers=self.headers, cookies=self.cookie)

        # 检查响应状态
        if response.status_code == 200:
            logger.debug("预习列表获取成功")
            response_json = response.json()
            for i in response_json['resultObject']['items']:
                if i['preview_name'] == "课程设计":
                    self.preview_courseId = i['id']
            return response_json
        else:
            logger.error(f"预习列表获取失败，状态码: {response.status_code}")
            return None

    def get_preview_info(self, ):
        # 获取具体预习信息的请求 URL 和参数
        url = f"{self.host}/back/bxg/preview/info?previewId={self.preview_courseId}&t={self.getTimestamp()}"

        # 发送 GET 请求以获取具体预习信息
        response = requests.get(url, headers=self.headers, cookies=self.cookie)

        # 检查响应状态
        if response.status_code == 200:
            logger.debug("预习信息获取成功")
            response_json = response.json()
            for i in response_json['resultObject']['chapters'][0]['points']:
                self.point_name = i['point_name']
                video_duration = i['video_duration']
                point_id = i['point_id']
                progress100 = i['progress100']
                if progress100 == 100:
                    continue
                point_list = self.generate_point(video_duration)
                logger.debug(f"开始观看-----{self.point_name}-----")
                for point in tqdm(point_list):
                    self.update_preview_progress(point_id, point)
                logger.debug(f"观看完成-----{self.point_name}-----")
            logger.success(f"《{self.courseName}》全部观看完成")
            return response_json
        else:
            logger.error(f"预习信息获取失败，状态码: {response.status_code}")
            return None

    def update_preview_progress(self, point_id, watched_duration):
        # 更新预习进度的请求 URL 和参数
        url = f"{self.host}/back/bxg/preview/updateProgress"
        data = {
            "previewId": self.preview_courseId,
            "pointId": point_id,
            "watchedDuration": watched_duration,
        }

        # 发送 POST 请求以更新进度
        response = requests.post(url, headers=self.headers, cookies=self.cookie, data=data)

        # 检查响应状态
        if response.status_code != 200:
            logger.error(f"更新预习进度失败，状态码: {response.status_code}")
        # else:
        #     print(f"成功更新预习进度 (预习Video: {self.point_name}\tResponse: {response.json()}")

    def run(self):
        self.login()
        if self.cookie:
            info = self.get_login_info()
            # logger.info(info)
            courses = self.get_courses()
            # logger.info(courses)
            preview_list = self.get_preview_list()
            # logger.info(preview_list)
            preview_info = self.get_preview_info()
            # logger.info(preview_info)


if __name__ == '__main__':
    ITManage = ITManage("这里填写账号", "这里填写密码", "这里填写课程名称")
    ITManage.run()