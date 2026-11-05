"""这是一个用于测试 Coding Agent read_file 能力的示例程序。"""

def calculate_fibonacci(n: int) -> list[int]:
    """计算斐波那契数列的前 n 项。"""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    
    fib = [0, 1]
    for _ in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib

if __name__ == "__main__":
    result = calculate_fibonacci(10)
    print("前 10 项斐波那契数:", result)
