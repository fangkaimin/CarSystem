from hyperlpr2 import pipline2 as pp
import cv2
#import sys
import mysql.connector as mysql
import os
import time

path = "D:\\car\\"
this_path = os.getcwd()
flag = os.path.exists(path)

list = os.listdir(path)
length = len(list)

"""
车牌识别部分，根据每个们的ip和照片id  进行识别判断，得到入口信息，出口信息 录入数据库
"""
count = 0
while (True):
    start = 0
    in_school = []
    car_school = []
    host = '192.168.58.16'
    user = 'root'
    password = 'root'
    db = 'hdcar'
    conn = mysql.connect(host=host, user=user, password=password, database=db)
    list = os.listdir(path)
    length = len(list)
    if length >= 1:
        for i in list:

            flag = False
            car_type = ""
            door_info = ""

            cursor = conn.cursor()
            sql = "select plate_number from car_images"
            cursor.execute(sql)
            result = cursor.fetchall() #获取进校的车辆车牌号
            for i in result:
                in_school.append(i[0])
            sql = "select plate_number from car_car_school"
            cursor.execute(sql)
            resuleset = cursor.fetchall()#获取校内车的所有车牌信息
            for i in resuleset:
                car_school.append(i[0])
            filename = path + list[start]
            image_info = list[start]
            if "192.168.1.1" in image_info:
                door_info = "正门"
            elif "192.168.1.2" in image_info:
                door_info = "西侧门"
            elif "192.168.1.3" in image_info:
                door_info = "东侧门"

            image = cv2.imread(filename)
            res, resultEnd, img = pp.SimpleRecognizePlate(image)
            cv2.imwrite('img.jpg',img)
            fp = open(this_path + '\img.jpg', 'rb')
            img = fp.read()
            fp.close()
            os.remove(this_path + '\img.jpg')
            new_plate = ''.join(resultEnd)
            new_plate = new_plate if (new_plate.strip() != "") else ""
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            if new_plate in in_school:
                # 更新car表  离开时间，出口信息； images 表 离开照片
                flag = False
            else:
                flag = True
                if new_plate in car_school:
                    car_type = "校内车辆"
                    #  flag = True
                else:
                    car_type = "社会车辆"
                    # print("校外")
            # 插入 car 表 车牌号码，进入时间，入口信息，金额，车辆类型，images表 进入照片，车牌号码
            if flag == True:
                sql = "insert into car_car (plate_number,in_date,car_type,enter_info) values (%s,%s,%s,%s)"
                cursor.execute(sql,[new_plate,now_time,car_type,door_info])
                conn.commit()
                sql = "insert into car_images (plate_number,entry_image) values (%s, %s)"
                cursor.execute(sql,[new_plate, mysql.Binary(img)])
                conn.commit()
            else:
                sql = "update car_car set out_date = %s, exit_info = %s where plate_number = %s"
                cursor.execute(sql,[now_time, door_info, new_plate])
                conn.commit()
                sql = "update car_images set exit_image = %s where plate_number = %s"
                cursor.execute(sql,[mysql.Binary(img), new_plate])
                conn.commit()
                sql = "insert into car_plate (plate_number)values (%s)"
                cursor.execute(sql,[new_plate])
                conn.commit()
            cursor.close()
            print(new_plate, now_time, car_type, door_info)
            # print(start, new_plate, now_time)
            os.remove(filename)
            start += 1
    time.sleep(2)
    # conn.close()
