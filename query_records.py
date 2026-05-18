"""查询通行记录（管理工具）
用法: python query_records.py [--stu 学号] [--dir in/out] [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import requests
from server.config import SERVER_PORT


def main():
    parser = argparse.ArgumentParser(description='查询通行记录')
    parser.add_argument('--stu', help='学号（模糊搜索）')
    parser.add_argument('--dir', choices=['in', 'out'], help='进出方向')
    parser.add_argument('--result', choices=['success', 'fail'], help='识别结果')
    parser.add_argument('--start', help='开始时间 YYYY-MM-DD')
    parser.add_argument('--end', help='结束时间 YYYY-MM-DD')
    parser.add_argument('--export', action='store_true', help='导出CSV')
    args = parser.parse_args()

    url = f"http://127.0.0.1:{SERVER_PORT}/api/record"
    if args.export:
        url += '/export'

    params = {k: v for k, v in vars(args).items() if v is not None and k != 'export'}
    resp = requests.get(url, params=params)

    if args.export:
        print(resp.text)
    else:
        data = resp.json()
        print(f"共 {data['total']} 条记录")
        for r in data['data']:
            print(f"  [{r['record_time']}] {r['student_name']}({r['stu_no']}) "
                  f"{'进门' if r['direction']=='in' else '出门'} "
                  f"{'成功' if r['result']=='success' else '失败'}")


if __name__ == '__main__':
    main()
