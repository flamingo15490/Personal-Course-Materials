from collections import defaultdict

scores=defaultdict(list)
judge_data=defaultdict(lambda: [0,0,0])
#强烈推荐为2，推荐为1，不推荐为0;用索引表示推荐指数
category=defaultdict(str)

#统计
try:
    with open('data/contestData.txt','r',encoding='utf-8') as f:
        for line in f.readlines():
            ID,others=line.strip().split(',')
            ID=int(ID)
            judges=[i for i in others.split()]
            for judge in judges:
                name,score0=judge.split('(')
                score=score0[:-1]
                if score=='推荐':
                    scores[ID].append(1)
                    judge_data[name][1]+=1
                elif score=='强烈推荐':
                    scores[ID].append(2)
                    judge_data[name][2]+=1
                elif score=='不推荐':
                    scores[ID].append(0)
                    judge_data[name][0]+=1
except FileNotFoundError:
        print(f"错误：找不到文件")
except Exception as e:
        print(f"读取文件时出错: {e}")

try:
    with open('data/work_cat.txt','r',encoding='utf-8') as f:
        title=f.readline().strip()
        for line in f.readlines():
            ID,kind=line.strip().split(',')
            ID=int(ID)
            category[ID]=kind
except FileNotFoundError:
        print(f"错误：找不到文件")
except Exception as e:
        print(f"读取文件时出错: {e}")


#输出
with open('runResult00.txt', 'w', encoding='utf-8') as file:
    file.write('作品编号 得分构型 作品类别\n')
    for ID in scores.keys():
        file.write(f"{ID}  {''.join(map(str,sorted(scores[ID],reverse=True)))}  {category[ID]}\n")

with open('runResult01.txt', 'w', encoding='utf-8') as file:
    file.write('姓名 强烈推荐 推荐 不推荐 \n')
    for ID in judge_data.keys():
        file.write(f'{ID}  {judge_data[ID][2]}  {judge_data[ID][1]}  {judge_data[ID][0]}\n')