import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

class BabelDOCClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def translate_pdf(
        self,
        pdf_path: str,
        lang_in: Optional[str] = None,
        lang_out: Optional[str] = None,
        qps: Optional[int] = None,
        no_dual: Optional[bool] = None,
        no_mono: Optional[bool] = None,
        watermark_output_mode: Optional[str] = None
    ) -> str:
        """
        提交PDF翻译任务
        
        Args:
            pdf_path: PDF文件路径
            lang_in: 源语言代码 (可选，使用服务器默认配置)
            lang_out: 目标语言代码 (可选，使用服务器默认配置)
            qps: 每秒请求数限制 (可选，使用服务器默认配置)
            no_dual: 不生成双语PDF (可选，使用服务器默认配置)
            no_mono: 不生成单语PDF (可选，使用服务器默认配置)
            watermark_output_mode: 水印模式 (可选，使用服务器默认配置)
        
        Returns:
            任务ID
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        files = {
            'file': ('document.pdf', open(pdf_path, 'rb'), 'application/pdf')
        }
        
        data = {}
        if lang_in is not None:
            data['lang_in'] = lang_in
        if lang_out is not None:
            data['lang_out'] = lang_out
        if qps is not None:
            data['qps'] = qps
        if no_dual is not None:
            data['no_dual'] = no_dual
        if no_mono is not None:
            data['no_mono'] = no_mono
        if watermark_output_mode is not None:
            data['watermark_output_mode'] = watermark_output_mode
        
        try:
            response = self.session.post(
                f"{self.base_url}/translate",
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            return result['task_id']
        finally:
            files['file'][1].close()
    
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取翻译任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态信息
        """
        response = self.session.get(f"{self.base_url}/status/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id: str, check_interval: int = 5, timeout: int = 3600) -> Dict[str, Any]:
        """
        等待翻译任务完成
        
        Args:
            task_id: 任务ID
            check_interval: 检查间隔秒数 (默认: 5)
            timeout: 超时时间秒数 (默认: 3600)
        
        Returns:
            最终任务状态
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_status(task_id)
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            print(f"任务状态: {status['status']} | 进度: {status['progress']:.1f}% | {status['message']}")
            time.sleep(check_interval)
        
        raise TimeoutError(f"任务 {task_id} 在 {timeout} 秒内未完成")
    
    def download_result(self, task_id: str, file_type: str, output_path: str) -> bool:
        """
        下载翻译结果文件
        
        Args:
            task_id: 任务ID
            file_type: 文件类型 ("dual" 或 "mono")
            output_path: 输出文件路径
        
        Returns:
            下载是否成功
        """
        response = self.session.get(f"{self.base_url}/download/{task_id}/{file_type}")
        
        if response.status_code == 404:
            return False
        
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    
    def translate_and_download(
        self,
        pdf_path: str,
        output_dir: str,
        lang_in: Optional[str] = None,
        lang_out: Optional[str] = None,
        qps: Optional[int] = None,
        no_dual: Optional[bool] = None,
        no_mono: Optional[bool] = None,
        watermark_output_mode: Optional[str] = None,
        check_interval: int = 5,
        timeout: int = 3600
    ) -> Dict[str, str]:
        """
        完整的翻译流程：提交任务 -> 等待完成 -> 下载结果
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            其他参数同 translate_pdf 方法
        
        Returns:
            下载的文件路径字典 {"dual": "path", "mono": "path"}
        """
        print(f"正在提交翻译任务: {pdf_path}")
        task_id = self.translate_pdf(
            pdf_path=pdf_path,
            lang_in=lang_in,
            lang_out=lang_out,
            qps=qps,
            no_dual=no_dual,
            no_mono=no_mono,
            watermark_output_mode=watermark_output_mode
        )
        
        print(f"任务已创建，ID: {task_id}")
        
        print("等待翻译完成...")
        final_status = self.wait_for_completion(task_id, check_interval, timeout)
        
        if final_status['status'] != 'completed':
            raise Exception(f"翻译失败: {final_status['message']}")
        
        print("翻译完成，正在下载结果...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = {}
        
        for file_type in ['dual', 'mono']:
            if file_type in final_status['result_files']:
                filename = f"{Path(pdf_path).stem}.{file_type}.pdf"
                output_file = output_path / filename
                
                if self.download_result(task_id, file_type, str(output_file)):
                    downloaded_files[file_type] = str(output_file)
                    print(f"已下载 {file_type} 文件: {output_file}")
        
        return downloaded_files
    
    def health_check(self) -> bool:
        """
        检查服务健康状态
        
        Returns:
            服务是否健康
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_server_config(self) -> Dict[str, Any]:
        """
        获取服务器配置信息
        
        Returns:
            服务器配置信息
        """
        response = self.session.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()

def main():
    """命令行客户端示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BabelDOC Translation Client")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出目录")
    parser.add_argument("--server-url", default="http://localhost:8000", help="服务器URL")
    parser.add_argument("--lang-in", help="源语言 (可选，使用服务器默认)")
    parser.add_argument("--lang-out", help="目标语言 (可选，使用服务器默认)")
    parser.add_argument("--qps", type=int, help="每秒请求数 (可选，使用服务器默认)")
    parser.add_argument("--no-dual", action="store_true", help="不生成双语PDF")
    parser.add_argument("--no-mono", action="store_true", help="不生成单语PDF")
    parser.add_argument("--watermark-mode", choices=["watermarked", "no_watermark", "both"], 
                       help="水印模式 (可选，使用服务器默认)")
    
    args = parser.parse_args()
    
    client = BabelDOCClient(args.server_url)
    
    if not client.health_check():
        print(f"错误: 无法连接到服务器 {args.server_url}")
        return
    
    # 显示服务器配置
    try:
        server_config = client.get_server_config()
        print("服务器配置:")
        print(f"  模型: {server_config['config']['openai_model']}")
        print(f"  默认语言: {server_config['config']['default_lang_in']} -> {server_config['config']['default_lang_out']}")
        print(f"  QPS: {server_config['config']['qps']}")
        print()
    except Exception as e:
        print(f"获取服务器配置失败: {e}")
    
    try:
        downloaded_files = client.translate_and_download(
            pdf_path=args.pdf_path,
            output_dir=args.output_dir,
            lang_in=args.lang_in,
            lang_out=args.lang_out,
            qps=args.qps,
            no_dual=args.no_dual,
            no_mono=args.no_mono,
            watermark_output_mode=args.watermark_mode
        )
        
        print(f"\n翻译完成! 下载的文件:")
        for file_type, path in downloaded_files.items():
            print(f"  {file_type}: {path}")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()