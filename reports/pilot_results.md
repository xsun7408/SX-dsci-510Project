# API 采集与完整度检查：300 条试采样

## 验证结果

- 20 条冒烟测试：20 成功、0 失败。
- 三部门试采样：300 成功、0 缺失，每部门 100 条。
- 两组样本分别重复运行：均未发出网络请求，缓存内容未改变。
- 共享缓存共 313 条唯一记录；20 条与 300 条清单并非包含关系，因此不能把整个缓存当作 300 条样本。
- 4 项采集逻辑单元测试通过；完整度脚本另验证了按清单筛选、空白字符串、缺失 ID 和负年份。

## 字段缺失率

| 部门 | 样本量 | culture | country | medium | artistNationality | 起止年份字段 |
|---|---:|---:|---:|---:|---:|---:|
| Asian Art | 100 | 0% | 100% | 0% | 70% | 0% |
| European Paintings | 100 | 100% | 100% | 0% | 0% | 0% |
| Greek and Roman Art | 100 | 3% | 100% | 0% | 100% | 0% |

“缺失”指字段不存在、null 或空白字符串，不能据此断言年份均可用于分析。

## 日期检查

- 96 条起始年份为负数。
- 3 条起始年份为 0，不能统一作为缺失删除：
  - 71838、71575：objectDate 为空且起止年份均为 0，需作为疑似未知日期核查。
  - 257827：objectDate 为 late 1st century BCE–early 1st century CE，起止年份为 0 和 25，需保留跨公元边界的日期含义。
- 14 条日期区间超过 500 年；需说明用起始年份归入世纪可能产生偏差。
- 未发现起始年份大于结束年份。

## 请求问题与修正

最初 0.25 秒间隔的扩大采集出现连续 HTTP 403，已中止并保留缓存。
暂停后的单次诊断请求恢复 200，原因未确定，不能断言为官方速率上限。
将默认间隔改为 1 秒，加入连续三次 403 自动停止保护后，沿原清单续抓成功。
没有更换 IP、绕过代理、替换失败 ID 或重新抽样。

## 下一步

1. Q1 和 Q2 可继续开展，但需处理未知日期、跨公元边界与宽日期区间。
2. Q3 暂不做三部门 artistNationality 多样性比较；country 在本样本全部缺失，也不能用作替代。
3. culture 可用于 Asian Art 与 Greek and Roman Art 的子样本研究；European Paintings 必须报告该字段不适用/未记录的限制，不能把缺失解释为没有文化。
4. 在确定 Q3 和日期规则后，再扩大到目标 3,000 条；本次未运行完整采集。

## 复现

在仓库目录执行：

```bash
/workspace/met-venv/bin/python acquire.py --count 20
/workspace/met-venv/bin/python acquire.py --count 300 --interval 1
/workspace/met-venv/bin/python inspect_quality.py data/sample_300_510.json
```

完整度表：data/sample_300_510.quality.csv。
抽样清单：data/sample_300_510.json。
原始记录：data/objects.jsonl（包括其他试采样，以清单筛选）。
原始数据及日志在 .gitignore 中；本次没有 commit、push 或发布环境。
