#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智邦国际ERP API完整解析工具
解析用户手动复制的API数据，生成结构化文档
"""

import re
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

class ERPAPIParser:
    """ERP API解析器"""
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.apis = []
        self.categories = defaultdict(list)
        
    def parse(self):
        """解析API文档"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 先找到所有"首页"开头的行
        lines = content.split('\n')
        api_starts = []
        
        for i, line in enumerate(lines):
            if line.startswith('首页') and '调用方式' in '\n'.join(lines[i:i+5]):
                api_starts.append(i)
        
        print(f"📄 发现 {len(api_starts)} 个API起始位置")
        
        # 分割成API块
        for i, start in enumerate(api_starts):
            end = api_starts[i + 1] if i + 1 < len(api_starts) else len(lines)
            block = '\n'.join(lines[start:end])
            
            api_info = self._parse_api_block(block)
            if api_info:
                self.apis.append(api_info)
                
                # 分类
                category = api_info.get('category', '未分类')
                self.categories[category].append(api_info)
        
        print(f"✅ 成功解析 {len(self.apis)} 个API接口")
        return self.apis
    
    def _parse_api_block(self, block: str) -> Dict[str, Any]:
        """解析单个API块"""
        api = {}
        
        try:
            # 1. 提取面包屑导航和API名称
            breadcrumb_match = re.search(r'首页(.*?)$', block, re.MULTILINE)
            if breadcrumb_match:
                breadcrumb = breadcrumb_match.group(1)
                parts = [p.strip() for p in breadcrumb.split('对接') if p.strip()]
                
                if len(parts) > 0:
                    api['breadcrumb'] = breadcrumb.strip()
                    api['category'] = parts[0] if len(parts) > 0 else '未分类'
                    api['subcategory'] = parts[1] if len(parts) > 1 else ''
                    
                    # 下一行是API名称
                    lines = block.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('首页'):
                            if i + 1 < len(lines):
                                api['name'] = lines[i + 1].strip()
                            break
            
            # 2. 提取调用方式
            method_match = re.search(r'调用方式：\s*(.*?)$', block, re.MULTILINE)
            if method_match:
                api['method'] = method_match.group(1).strip()
            
            # 3. 提取接口地址
            url_match = re.search(r'接口地址：\s*(.*?)$', block, re.MULTILINE)
            if url_match:
                api['url'] = url_match.group(1).strip()
            
            # 4. 提取请求类型
            content_type_match = re.search(r'请求类型：\s*(.*?)$', block, re.MULTILINE)
            if content_type_match:
                api['content_type'] = content_type_match.group(1).strip()
            
            # 5. 提取请求参数
            api['request_params'] = self._parse_parameters(block, '请求参数')
            
            # 6. 提取输出参数
            api['response_params'] = self._parse_parameters(block, '输出参数')
            
            # 7. 提取请求范例
            api['request_example'] = self._extract_json_example(block, '请求范例')
            
            # 8. 提取返回结果说明
            api['response_description'] = self._parse_response_description(block)
            
            # 9. 提取注意事项
            notice_match = re.search(r'注意事项：\s*\n(.*?)(?=\n首页|\Z)', block, re.DOTALL)
            if notice_match:
                api['notice'] = notice_match.group(1).strip()
            
            return api if api.get('name') else None
            
        except Exception as e:
            print(f"⚠️  解析API块失败: {str(e)}")
            return None
    
    def _parse_parameters(self, block: str, section_name: str) -> List[Dict[str, str]]:
        """解析参数表格"""
        params = []
        
        # 找到参数表格部分
        pattern = f'{section_name}\\s*\\n字段名称\\s+类型\\s+必填\\s+描述\\s*\\n(.*?)(?=请求范例|输出参数|返回结果|注意事项|\\Z)'
        match = re.search(pattern, block, re.DOTALL)
        
        if not match:
            # 尝试简化版（没有必填列）
            pattern = f'{section_name}\\s*\\n字段名称\\s+类型\\s+描述\\s*\\n(.*?)(?=请求范例|Json示例|\\Z)'
            match = re.search(pattern, block, re.DOTALL)
        
        if match:
            param_text = match.group(1)
            lines = param_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('请求范例') or line.startswith('JsonC#'):
                    continue
                
                # 解析参数行
                parts = re.split(r'\t+', line)
                if len(parts) >= 3:
                    param = {
                        'name': parts[0].strip(),
                        'type': parts[1].strip(),
                        'required': parts[2].strip() if len(parts) >= 4 else '',
                        'description': parts[3].strip() if len(parts) >= 4 else parts[2].strip()
                    }
                    
                    # 处理多行描述
                    if '来自接口：' in param['description']:
                        param['source_api'] = param['description'].split('来自接口：')[1].strip()
                    
                    params.append(param)
        
        return params
    
    def _extract_json_example(self, block: str, section_name: str) -> str:
        """提取JSON示例"""
        # 查找JSON代码块
        pattern = f'{section_name}.*?\\{{(.*?)\\}}'
        match = re.search(pattern, block, re.DOTALL)
        
        if match:
            json_text = '{' + match.group(1) + '}'
            # 清理注释
            json_text = re.sub(r'//.*?$', '', json_text, flags=re.MULTILINE)
            return json_text.strip()
        
        return ''
    
    def _parse_response_description(self, block: str) -> Dict[str, Any]:
        """解析返回结果描述"""
        description = {}
        
        # 提取返回结果类型
        type_match = re.search(r'(BillClass|MessageClass|SourceClass|ListClass)\s*[:：]', block)
        if type_match:
            description['type'] = type_match.group(1)
        
        # 提取类型说明
        desc_match = re.search(r'(BillClass|MessageClass|SourceClass|ListClass)\s*[:：]\s*(.*?)(?=\n\n|\nBillClass|\nMessageClass|\Z)', block, re.DOTALL)
        if desc_match:
            description['description'] = desc_match.group(2).strip()
        
        return description
    
    def generate_markdown_docs(self, output_dir: str = 'docs/erp_api'):
        """生成Markdown文档"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 生成总索引文档
        index_file = f'{output_dir}/智邦ERP_API完整索引.md'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write('# 智邦国际ERP API完整索引\n\n')
            f.write(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write(f'**总计**: {len(self.apis)} 个API接口\n\n')
            f.write('---\n\n')
            
            # 按分类组织
            f.write('## 📑 按分类浏览\n\n')
            for category, apis in sorted(self.categories.items()):
                f.write(f'### {category} ({len(apis)}个)\n\n')
                for api in apis:
                    f.write(f'- [{api["name"]}](#{self._slugify(api["name"])})\n')
                f.write('\n')
            
            f.write('---\n\n')
            f.write('## 📖 API详细说明\n\n')
            
            # 详细说明
            for api in self.apis:
                self._write_api_detail(f, api)
        
        print(f'✅ 生成索引文档: {index_file}')
        
        # 2. 按分类生成独立文档
        for category, apis in self.categories.items():
            category_file = f'{output_dir}/{self._safe_filename(category)}.md'
            with open(category_file, 'w', encoding='utf-8') as f:
                f.write(f'# {category}\n\n')
                f.write(f'**API数量**: {len(apis)} 个\n\n')
                f.write('---\n\n')
                
                for api in apis:
                    self._write_api_detail(f, api)
            
            print(f'✅ 生成分类文档: {category_file}')
        
        # 3. 生成快速参考表
        quick_ref_file = f'{output_dir}/API快速参考表.md'
        with open(quick_ref_file, 'w', encoding='utf-8') as f:
            f.write('# API快速参考表\n\n')
            f.write('| API名称 | 接口地址 | 请求方式 | 分类 |\n')
            f.write('|---------|----------|----------|------|\n')
            
            for api in self.apis:
                name = api.get('name', '')
                url = api.get('url', '')
                method = api.get('method', '')
                category = api.get('category', '')
                f.write(f'| {name} | {url} | {method} | {category} |\n')
        
        print(f'✅ 生成快速参考: {quick_ref_file}')
    
    def _write_api_detail(self, f, api: Dict[str, Any]):
        """写入API详细信息"""
        f.write(f'## {api.get("name", "未命名API")}\n\n')
        
        # 基本信息
        if api.get('breadcrumb'):
            f.write(f'**路径**: 首页{api["breadcrumb"]}\n\n')
        
        f.write(f'**调用方式**: {api.get("method", "")}\n\n')
        f.write(f'**接口地址**: `{api.get("url", "")}`\n\n')
        f.write(f'**请求类型**: `{api.get("content_type", "")}`\n\n')
        
        # 请求参数
        if api.get('request_params'):
            f.write('### 📥 请求参数\n\n')
            f.write('| 字段名称 | 类型 | 必填 | 描述 |\n')
            f.write('|----------|------|------|------|\n')
            
            for param in api['request_params']:
                name = param.get('name', '')
                ptype = param.get('type', '')
                required = param.get('required', '')
                desc = param.get('description', '').replace('\n', ' ')
                f.write(f'| {name} | {ptype} | {required} | {desc} |\n')
            
            f.write('\n')
        
        # 请求示例
        if api.get('request_example'):
            f.write('### 📤 请求示例\n\n')
            f.write('```json\n')
            f.write(api['request_example'])
            f.write('\n```\n\n')
        
        # 响应参数
        if api.get('response_params'):
            f.write('### 📨 响应参数\n\n')
            f.write('| 字段名称 | 类型 | 描述 |\n')
            f.write('|----------|------|------|\n')
            
            for param in api['response_params']:
                name = param.get('name', '')
                ptype = param.get('type', '')
                desc = param.get('description', '').replace('\n', ' ')
                f.write(f'| {name} | {ptype} | {desc} |\n')
            
            f.write('\n')
        
        # 响应类型说明
        if api.get('response_description'):
            rd = api['response_description']
            if rd.get('type'):
                f.write(f'**响应类型**: {rd["type"]}\n\n')
            if rd.get('description'):
                f.write(f'**类型说明**: {rd["description"]}\n\n')
        
        # 注意事项
        if api.get('notice'):
            f.write('### ⚠️  注意事项\n\n')
            f.write(f'{api["notice"]}\n\n')
        
        f.write('---\n\n')
    
    def generate_json_export(self, output_file: str):
        """生成JSON导出"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'apis': self.apis,
                'categories': {k: len(v) for k, v in self.categories.items()},
                'total_count': len(self.apis),
                'generated_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f'✅ 生成JSON导出: {output_file}')
    
    def generate_python_client(self, output_file: str):
        """生成Python客户端代码"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('#!/usr/bin/env python3\n')
            f.write('# -*- coding: utf-8 -*-\n')
            f.write('"""\n')
            f.write('智邦国际ERP API Python客户端\n')
            f.write(f'自动生成于: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('"""\n\n')
            f.write('import requests\n')
            f.write('from typing import Dict, List, Optional, Any\n\n')
            
            f.write('class ZhibangERPClient:\n')
            f.write('    """智邦ERP API客户端"""\n\n')
            f.write('    def __init__(self, base_url: str, session: str = None):\n')
            f.write('        self.base_url = base_url\n')
            f.write('        self.session = session\n\n')
            
            f.write('    def login(self, username: str, password: str, serialnum: str) -> Dict[str, Any]:\n')
            f.write('        """系统登录"""\n')
            f.write('        url = f"{self.base_url}/webapi/v3/ov1/login"\n')
            f.write('        payload = {\n')
            f.write('            "datas": [\n')
            f.write('                {"id": "user", "val": f"txt:{username}"},\n')
            f.write('                {"id": "password", "val": f"txt:{password}"},\n')
            f.write('                {"id": "serialnum", "val": f"txt:{serialnum}"}\n')
            f.write('            ]\n')
            f.write('        }\n')
            f.write('        response = requests.post(url, json=payload)\n')
            f.write('        result = response.json()\n')
            f.write('        if result.get("header", {}).get("status") == 0:\n')
            f.write('            self.session = result["header"]["session"]\n')
            f.write('        return result\n\n')
            
            # 生成常用API方法
            customer_apis = self.categories.get('销售栏目客户管理客户', [])
            for api in customer_apis[:10]:  # 生成前10个
                method_name = self._to_method_name(api['name'])
                f.write(f'    def {method_name}(self, **kwargs) -> Dict[str, Any]:\n')
                f.write(f'        """{api["name"]}"""\n')
                f.write(f'        url = "{api.get("url", "")}"\n')
                f.write('        payload = {\n')
                f.write('            "session": self.session,\n')
                f.write('            "datas": [\n')
                f.write('                {"id": key, "val": value} for key, value in kwargs.items()\n')
                f.write('            ]\n')
                f.write('        }\n')
                f.write('        response = requests.post(url, json=payload)\n')
                f.write('        return response.json()\n\n')
        
        print(f'✅ 生成Python客户端: {output_file}')
    
    def generate_integration_guide(self, output_file: str):
        """生成对接指南"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# 智邦ERP与微信中台对接指南\n\n')
            f.write(f'**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write('---\n\n')
            
            f.write('## 🎯 核心对接场景\n\n')
            
            scenarios = [
                {
                    'title': '1. 客户信息同步',
                    'description': '从微信中台同步客户信息到ERP系统',
                    'apis': ['单位客户添加', '个人客户添加', '客户列表', '客户详情', '客户修改'],
                    'fields': ['name', 'mobile', 'weixinAcc', 'ly', 'khid', 'address', 'intro']
                },
                {
                    'title': '2. 跟进记录同步',
                    'description': '同步微信沟通记录到ERP跟进记录',
                    'apis': ['洽谈进展', '联系人添加', '联系人列表'],
                    'fields': ['ord', 'intro', 'person_name', 'mobile', 'email']
                },
                {
                    'title': '3. 客户分配管理',
                    'description': '根据中台评分自动分配客户给销售',
                    'apis': ['客户指派', '客户申请', '客户审批', '客户收回'],
                    'fields': ['ord', 'member1', 'member2']
                },
                {
                    'title': '4. 客户来源追踪',
                    'description': '标记客户来源为微信渠道',
                    'apis': ['客户添加', '客户修改'],
                    'fields': ['ly']  # 客户来源字段
                }
            ]
            
            for scenario in scenarios:
                f.write(f'### {scenario["title"]}\n\n')
                f.write(f'{scenario["description"]}\n\n')
                f.write(f'**相关API**: {", ".join(scenario["apis"])}\n\n')
                f.write(f'**关键字段**: `{", ".join(scenario["fields"])}`\n\n')
                
                # 查找对应的API详情
                for api_name in scenario["apis"]:
                    matching_apis = [a for a in self.apis if api_name in a.get('name', '')]
                    if matching_apis:
                        api = matching_apis[0]
                        f.write(f'#### {api["name"]}\n\n')
                        f.write(f'- **接口**: `{api.get("url", "")}`\n')
                        f.write(f'- **方式**: {api.get("method", "")}\n')
                        
                        # 列出关键参数
                        if api.get('request_params'):
                            key_params = [p for p in api['request_params'] if p['name'] in scenario['fields']]
                            if key_params:
                                f.write('- **关键参数**:\n')
                                for p in key_params:
                                    f.write(f'  - `{p["name"]}` ({p["type"]}): {p["description"]}\n')
                        f.write('\n')
                
                f.write('---\n\n')
            
            f.write('## 💡 实施建议\n\n')
            f.write('### 数据映射表\n\n')
            f.write('| 微信中台字段 | ERP字段 | 说明 |\n')
            f.write('|--------------|---------|------|\n')
            f.write('| contact.name | name | 客户名称 |\n')
            f.write('| contact.phone | mobile | 手机号码 |\n')
            f.write('| contact.wechat_id | weixinAcc | 微信号 |\n')
            f.write('| contact.company | name (单位客户) | 公司名称 |\n')
            f.write('| contact.source | ly | 客户来源（设置为"微信"） |\n')
            f.write('| contact.notes | intro | 备注信息 |\n')
            f.write('| thread.score | jz | 价值评估 |\n')
            f.write('| signal.content | product | 客户简介/沟通记录 |\n\n')
            
            f.write('### 同步策略\n\n')
            f.write('1. **准入条件**:\n')
            f.write('   - 手机号已验证\n')
            f.write('   - 客户名称完整\n')
            f.write('   - 通过白名单评分（score >= 60）\n\n')
            
            f.write('2. **同步时机**:\n')
            f.write('   - 客户从灰名单升级到白名单时\n')
            f.write('   - 客户完成首次成交时\n')
            f.write('   - 手动触发同步\n\n')
            
            f.write('3. **冲突解决**:\n')
            f.write('   - ERP客户编号(khid)为主键\n')
            f.write('   - 手机号去重\n')
            f.write('   - 微信号补充到ERP\n\n')
        
        print(f'✅ 生成对接指南: {output_file}')
    
    @staticmethod
    def _slugify(text: str) -> str:
        """生成URL友好的slug"""
        return re.sub(r'[^\w\u4e00-\u9fa5]+', '-', text).strip('-').lower()
    
    @staticmethod
    def _safe_filename(text: str) -> str:
        """生成安全的文件名"""
        return re.sub(r'[^\w\u4e00-\u9fa5]+', '_', text).strip('_')
    
    @staticmethod
    def _to_method_name(api_name: str) -> str:
        """转换为Python方法名"""
        # 简单映射
        mapping = {
            '客户列表': 'get_customer_list',
            '客户详情': 'get_customer_detail',
            '单位客户添加': 'add_company_customer',
            '个人客户添加': 'add_personal_customer',
            '客户修改': 'update_customer',
            '客户指派': 'assign_customer',
            '客户收回': 'recall_customer',
        }
        return mapping.get(api_name, api_name.lower().replace(' ', '_'))


def main():
    """主函数"""
    print('🚀 智邦ERP API完整解析工具')
    print('=' * 60)
    
    # 初始化解析器
    parser = ERPAPIParser('用户手动复制的API数据.md')
    
    # 解析API
    apis = parser.parse()
    
    print('\n📊 解析统计:')
    print(f'  - 总API数量: {len(apis)}')
    print(f'  - 分类数量: {len(parser.categories)}')
    
    # 生成文档
    print('\n📝 生成文档...')
    parser.generate_markdown_docs('docs/erp_api')
    
    # 生成JSON导出
    parser.generate_json_export('docs/erp_api/智邦ERP_API完整数据.json')
    
    # 生成Python客户端
    parser.generate_python_client('erp_sync/zhibang_client.py')
    
    # 生成对接指南
    parser.generate_integration_guide('docs/erp_api/微信中台ERP对接指南.md')
    
    print('\n✅ 全部完成!')
    print('\n📂 生成的文件:')
    print('  - docs/erp_api/智邦ERP_API完整索引.md')
    print('  - docs/erp_api/API快速参考表.md')
    print('  - docs/erp_api/智邦ERP_API完整数据.json')
    print('  - erp_sync/zhibang_client.py')
    print('  - docs/erp_api/微信中台ERP对接指南.md')


if __name__ == '__main__':
    main()

