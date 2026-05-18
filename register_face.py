"""一次性注册人脸照片（管理工具）
用法: python register_face.py <学号> <姓名> <照片路径>
示例: python register_face.py 20231113513 张三 photo.jpg
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import requests
from server.config import SERVER_PORT

SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    stu_no = sys.argv[1]
    name = sys.argv[2]
    photo_path = sys.argv[3]

    if not os.path.exists(photo_path):
        print(f"照片不存在: {photo_path}")
        sys.exit(1)

    # 1. 创建学生
    resp = requests.post(
        f"{SERVER_URL}/api/student",
        json={'stu_no': stu_no, 'name': name}
    )
    if resp.status_code == 409:
        # 已存在，查询 student_id
        resp2 = requests.get(f"{SERVER_URL}/api/student?keyword={stu_no}")
        data = resp2.json()
        if data['total'] > 0:
            student_id = data['data'][0]['id']
            print(f"学生已存在: id={student_id}")
        else:
            print("查询学生失败")
            sys.exit(1)
    elif resp.status_code == 201:
        student_id = resp.json()['id']
        print(f"学生创建成功: id={student_id}")
    else:
        print(f"创建学生失败: {resp.json()}")
        sys.exit(1)

    # 2. 上传照片注册人脸
    with open(photo_path, 'rb') as f:
        files = {'photo': (os.path.basename(photo_path), f, 'image/jpeg')}
        resp = requests.post(
            f"{SERVER_URL}/api/face/register",
            data={'student_id': str(student_id)},
            files=files
        )
    if resp.status_code == 200:
        data = resp.json()
        print(f"人脸注册成功！版本号: {data.get('feature_version')}")
    else:
        print(f"人脸注册失败: {resp.json()}")
        sys.exit(1)


if __name__ == '__main__':
    main()
