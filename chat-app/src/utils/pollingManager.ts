/**
 * 轮询管理器
 * 用于定期执行指定的回调函数，实现自动刷新功能，监测文件或网页的上传状态。
 */
export class PollingManager {
  private intervalId: number | null = null;
  private callback: () => Promise<void>;
  private intervalMs: number;
  private isPolling: boolean = false;
  
  /**
   * 创建轮询管理器
   * @param callback 要定期执行的回调函数
   * @param intervalMs 轮询间隔（毫秒）
   */
  constructor(callback: () => Promise<void>, intervalMs: number = 5000) {
    this.callback = callback;
    this.intervalMs = intervalMs;
  }
  
  /**
   * 启动轮询
   */
  start(): void {
    if (this.isPolling) return;
    
    this.isPolling = true;
    
    // 立即执行一次回调
    this.executeCallback();
    
    // 设置定时器定期执行回调
    this.intervalId = window.setInterval(() => {
      this.executeCallback();
    }, this.intervalMs);
  }
  
  /**
   * 停止轮询
   */
  stop(): void {
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isPolling = false;
  }
  
  /**
   * 执行回调函数并处理可能的错误
   */
  private async executeCallback(): Promise<void> {
    try {
      await this.callback();
    } catch (error) {
      console.error('轮询回调执行失败:', error);
    }
  }
  
  /**
   * 更改轮询间隔
   * @param newIntervalMs 新的轮询间隔（毫秒）
   */
  setInterval(newIntervalMs: number): void {
    this.intervalMs = newIntervalMs;
    
    // 如果正在轮询，重启轮询以应用新的间隔
    if (this.isPolling) {
      this.stop();
      this.start();
    }
  }
  
  /**
   * 手动触发一次回调执行
   */
  trigger(): void {
    this.executeCallback();
  }
} 