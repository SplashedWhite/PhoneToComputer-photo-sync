import os
import win32com.client
import pythoncom
# 暂时忽略pylance警告，win32可以运行
from win32com.shell import shellcon # type: ignore
import time

# 判断是不是MTP设备
def is_mtp_device(item):
    """判断是不是MTP设备"""

    # 手机中英文类型关键词库（可扩展）
    mtp_keywords = [
        "移动电话",    # 中文描述
        "Mobile Device",  # 英文描述
        "Portable Device" # 某些系统可能用这种描述
    ]
    
    # 排除本地存储关键词（动态适应语言）
    local_disk_keywords = [
        "本地磁盘",    # 中文
        "Local Disk",  # 英文
        "Network Drive", # 网络驱动器（额外过滤） 
        "DVD Drive"     # 光驱
    ]

    # 针对特殊情况的防御代码，如果发现个别设备误判，可以添加设备名排除规则：
    blacklist_names = [
    "CD Drive",      # 光驱
    "VirtualBox",    # 虚拟机磁盘
    "RamDisk"        # 内存虚拟磁盘
    ]
    #排除黑名单
    if any(name in item.Name for name in blacklist_names):
        return False
    
    """
    #调试信息
    # 在is_mtp_device函数中添加打印：
    print(
        f"[调试] 设备名:{item.Name} "
        f"类型:{item.Type} "
        f"Path: {item.Path} "
        "——————————————"
    )
    """

    # 正常item.Type为本地磁盘，手机设备为移动电话
    # 核心判断逻辑
    return (
        any(kw in item.Type for kw in mtp_keywords) and
        not any(kw in item.Type for kw in local_disk_keywords)
    )

# 增加路径特征作为辅助判断
def is_mtp_path(item):

    """通过CLSID路径格式判断（MTP设备路径含特殊标识符）"""
    # 我的电脑 CLSID: 20D04FE0-3AEA-1069-A2D8-08002B30309D
    if not item.Path.startswith("::{20D04FE0"):
        return False
    
    # """
    # 通过路径特征判断
    # mtp_path_patterns = [
    #     r"\\\?\usb#",        # USB设备路径特征
    #     r"\\\?\wpdbusenum#"  # Windows Portable Device枚举路径
    # ] # 用引号注释报错是因为斜杠
    # path = item.Path.lower()
    # return any(pattern in path for pattern in mtp_path_patterns)
    # """

    """
    #路径代码调试信息
    print(f"[路径诊断] 当前设备: {item.Name}")
    print(f"  原始路径: {repr(item.Path)}")  # 使用repr显示转义符
    print(f"  包含::? {'::' in item.Path}")
    print(f"  以::{{开头? {item.Path.startswith('::{')}")
    # ...其他逻辑...
    """

    """通过路径特征判断"""
    # 关键后缀：包含MTP设备特有的接口标识
    # 过滤系统级命名空间
    if ("::" in item.Path)  and  (item.Path.startswith("::{"))  and  (("usb#vid_" in item.Path  or  "wpdbusenum#" in item.Path)):
        #当路径包含“::”且以“::{”开头；并且包含MTP设备特有的接口标识
        return True
    else:
        return False
    
    """
    #单独通过CLSID路径结构判断的返回代码
    return "::" in item.Path and not item.Path.startswith("::{")  # 过滤系统级命名空间
    """
    
    """
    MTP设备的Shell路径特征示例："::{20D04FE0-3AEA-1069-A2D8-08002B30309D}\\\\::{UUID}"
    本地磁盘路径："C:" 或 "D:"
    """

#寻找设备
#枚举存储设备
def enum_mtp_devices():
    """获取Windows Shell中的"此电脑"节点（所有存储设备的根），然后调用判断mtp设备函数找出mtp设备"""
    shell = win32com.client.Dispatch("Shell.Application")
    # 使用更通用的常量 CSIDL_DRIVES 表示 "此电脑"
    namespace = shell.Namespace(shellcon.CSIDL_DRIVES)
    
    #替换代码，和return代码一样
    devices = []
    for item in namespace.Items():
        """ 函数is_mtp_device(item)的调试信息粘贴到此处也行 """
        if  is_mtp_device(item) or is_mtp_path(item):
            # 最终合并判断逻辑
            devices.append(item)
            print("检测到的设备名称:", item.Name) 
    return devices

    #以下为for循环代替代码
    """
    return [item for item in namespace.Items() if is_mtp_device(item)]
    """

#复制文件
def copy_qq_photos(device_item, local_backup_dir):
    """从手机 Pictures/QQ 文件夹复制文件"""
    # 1. 进入内部存储或主目录
    internal_storage = None
    for folder in device_item.GetFolder.Items():
        if "内部存储" in folder.Name or "Internal Storage" in folder.Name:
            internal_storage = folder
            break
    if not internal_storage:
        print("错误：未找到内部存储目录")
        print("当前可用目录:")
        for f in device_item.GetFolder.Items():
            print(f"- {f.Name} ({f.Type})")
        return

    # 2. 进入 Pictures 文件夹
    pictures_folder = None
    for folder in internal_storage.GetFolder.Items():
        if "Pictures" in folder.Name or "图片" in folder.Name:
            pictures_folder = folder
            # 测试，临时修改文件存放路径
            # local_backup_dir = r"F:\code\syc\1"
            copy_mtp_folder(pictures_folder.GetFolder, local_backup_dir)
            return
            break
    return
    if not pictures_folder:
        print("错误：未找到 Pictures/图片 目录")
        return
    
    # 3. 进入 QQ 文件夹
    qq_folder = None
    for folder in pictures_folder.GetFolder.Items():
        if folder.Name == "QQ":
            qq_folder = folder
            break
    if not qq_folder:
        print("错误：未找到 QQ 目录")
        return
    
    # 4. 仅复制前200个文件测试
    max_files = 200  #最大处理文件数量
    copied = 0       # [处理] 计数器
    successful = 0   # [成功] 计数器
    failures = 0     # [失败] 计数器
    skip = 0         # [跳过] 计数器

    for item in qq_folder.GetFolder.Items():
        if copied >= max_files:
            print("达到复制上限，停止处理")
            break

        if item.IsFolder: # 如果是文件夹
            print(f"[跳过] 目录(文件夹)不被处理: {item.Name}")
            continue # 直接跳过当前文件夹

        #本地文件保存路径+文件名
        local_path = os.path.join(local_backup_dir, item.Name)

        if os.path.exists(local_path):
            # 新增对文件存在的反馈
            print(f"[跳过] 文件已存在: {item.Name}")
            skip = skip + 1 # [跳过] 计数器
            continue  # 直接跳过当前文件
        try:
            # 复制文件到本地目录
            target_folder = win32com.client.Dispatch("Shell.Application").Namespace(local_backup_dir)
            target_folder.CopyHere(item)
            copied += 1 # [处理] 计数器
            print(f"[成功] 已复制 {copied}/{max_files}: {item.Name}")
        except Exception as e:
            print(f"[错误] 复制失败: {item.Name}，原因: {str(e)}")
            failures = failures + 1 # [失败] 计数器

    successful = copied - failures # [成功] 计数器
    
    print(f"【总结】 总计处理文件数: {copied} ,成功: {successful} ,失败: {failures} ")
    print(f"【总结】 重复文件数: {skip} ,没有处理")


    """
    # 1.在调用 CopyHere 时添加参数 16=自动重命名（避免冲突）
    target_folder.CopyHere(item, 16)  # ✅ 强制自动重命名
    此时即使文件存在，复制后也会生成新文件，确保每次都能触发复制动作。
    # 2.使用参数 4|16（无UI + 自动重命名）
    target_namespace.CopyHere(item, 4 | 16)
    """

#判断是否为隐藏文件夹
def is_hidden_folder(item) -> bool:
    """判断是否为隐藏文件夹（根据 MTP 设备的惯例）"""
    if not item.IsFolder: # 如果不是文件夹
        print(f"{item.Name}不是文件夹")
        return False
    # 方案一: 根据文件名判断（适用于普通情形）
    if item.Name.startswith("."):
        return True
    return False
    """
    # 方案二: 检查系统隐藏属性（需要属性支持）
    #不可用
    try:
        attrs = item.ExtendedProperty("System.FileAttributes")
        return attrs & 2 == 2  # FILE_ATTRIBUTE_HIDDEN
    except:  # 某些设备可能无法获取该属性
        return False
    return False
    """

#备份主函数
def backup_qq_photos_test():
    pythoncom.CoInitialize()
    devices = enum_mtp_devices()#decives为一个数组
    #devices里面是过滤后的MTP设备
    if not devices:#如果devices为空
        print("未检测到设备: 请检查手机连接模式")
        return
    
    backup_dir = r"F:\code\syc\1"
    #递归创建多层目录
    os.makedirs(backup_dir, exist_ok=True)# exist_ok=True：目标目录已存在的情况下不会触发 FileExistsError 异常
    
    device = devices[0]
    print(f"正在从设备 [{device.Name}] 复制文件...")
    #防止随意复制，仅做测试
    # if input() == "1":
    
    # 测试隐藏文件夹判断
    # test_is_hidden(device, backup_dir)
    # return
    copy_qq_photos(device, backup_dir)
    pythoncom.CoUninitialize()
    print(f"测试完成！查看目录: {backup_dir}")

"""
主函数存放地点
"""

# 测试判断隐藏文件夹的函数
def test_is_hidden(device_item, local_backup_dir) :
    # 1. 进入内部存储或主目录
    internal_storage = None
    for folder in device_item.GetFolder.Items():
        if "内部存储" in folder.Name or "Internal Storage" in folder.Name:
            internal_storage = folder
            break
    if not internal_storage:
        print("错误：未找到内部存储目录")
        print("当前可用目录:")
        for f in device_item.GetFolder.Items():
            print(f"- {f.Name} ({f.Type})")
        return

    # 2. 进入 Pictures 文件夹
    pictures_folder = None
    for folder in internal_storage.GetFolder.Items():
        if "Pictures" in folder.Name or "图片" in folder.Name:
            pictures_folder = folder
            break
    if not pictures_folder:
        print("错误：未找到 Pictures/图片 目录")
        return

    hidden_folder_number = 0 # 隐藏文件夹计数器
    file_number = 0          # 其他文件计数器
    all_number = 0           #总计数器

    # 3. 遍历Picture文件夹下的所有文件
    for folder in pictures_folder.GetFolder.Items():

        all_number = all_number + 1

        if is_hidden_folder(folder):
            hidden_folder_number = hidden_folder_number + 1
            print(f"{folder.Name}是隐藏文件" )
        else:
            file_number = file_number + 1
            
    print(f"一共有{all_number}个文件夹和文件")
    print(f"一共有{hidden_folder_number}个隐藏文件夹")
    print(f"一共有{file_number}个其他文件")
    return 0

# 新增全局状态记录器
suspicious_folders = []
# 获取该层目录项（可能返回空列表）
def get_items_with_retry(folder, max_retries=3, initial_delay=0.5):
    """原有函数改进版"""
    retries = 0
    delay = 1  # 初始延迟1秒
    
    while retries < max_retries:
        try:
            items = list(folder.Items())
            if items:  # 有内容直接返回
                return (True, items)  # 元组新增状态位
        except pythoncom.com_error as e:
            if e.hresult == 0x800704C7:  # MTP设备未就绪错误码
                print(f"设备未就绪，等待 {delay:.1f}秒 后重试...")
                time.sleep(delay)
                delay *= 2
                retries += 1
            else:
                raise
        
        print(f"空目录重试中 ({retries+1}/{max_retries})")
        time.sleep(delay)
        delay *= 2
        retries +=1
    
    # 🔴 重要改动：达到重试上限仍未加载到内容
    # 记录设备路径到疑似列表
    try:
        folder_Name = folder.Title # 名称获取
        suspicious_folders.append(folder_Name)
    except:
        pass
    
    return (False, [])  # 第一个参数表示是否可信

# 获取该层目录项（可能返回空列表）
# def get_items_with_retry(folder, max_retries=3, initial_delay=0.5):
#     """延迟自适应的递归扫描"""
#     """获取文件夹项（含智能重试）"""
#     retries = 0
#     delay = initial_delay

#     while retries < max_retries:
#         try:
#             items = list(folder.Items())

            
#             if len(items) == 0:
#                 # 空目录可能是未加载完成导致
#                 time.sleep(delay)
#                 delay *= 2  # 每失败一次，延迟翻倍
#                 retries += 1
#                 continue
#             return items
#         except pythoncom.com_error as e:
#             if e.hresult == 0x800704C7:  # MTP设备未就绪错误码
#                 print(f"设备未就绪，等待 {delay:.1f}秒 后重试...")
#                 time.sleep(delay)
#                 delay *= 2
#                 retries += 1
#             else:
#                 raise
#     return 0
#     # raise TimeoutError("无法获取目录内容")

# 递归备份主函数
def copy_mtp_folder(mtp_namespace, local_base_dir, max_files=999999):
    """
    递归复制 MTP 文件夹内容（自动跳过隐藏文件夹）
    
    参数:
        mtp_namespace: 已定位的源文件夹 Shell 命名空间对象
        local_base_dir: 当前递归层级对应的本地目录路径

    # 添加类型验证调试代码
    print(f"Namespace类型验证: {type(mtp_namespace)}")
    print(f"可用方法: {dir(mtp_namespace)}")
    """
    
    shell = win32com.client.Dispatch("Shell.Application")
    copied = 0

    # 递归创建本地多层目录（如果不存在）
    os.makedirs(local_base_dir, exist_ok=True)# exist_ok=True：目标目录已存在的情况下不会触发 FileExistsError 异常
    local_namespace = shell.Namespace(local_base_dir)

    """改进后的复制逻辑"""
    # 获取目录项并检查可信度
    is_trustworthy, items = get_items_with_retry(mtp_namespace)
    # 🚩 直接记录本地备份路径 
    if not is_trustworthy and not items:
        suspicious_folders.append( os.path.abspath(local_base_dir) ) # 关键修改点
        # 防御性编程函数，可以去try catch
        # create_warning_marker(local_base_dir)
        return 0

    # 本地目录创建（保持原有逻辑）  
    os.makedirs(local_base_dir, exist_ok=True)

    """
    # 之前的代码
    # 创建本地空目录标记
    os.makedirs(local_base_dir, exist_ok=True)
    marker_file = os.path.join(local_base_dir, ".empty")
    
    if not is_trustworthy and len(items) ==0:
        # 📌 新增处理：疑似延迟空目录
        with open(marker_file, "w") as f:
            f.write("该目录可能在设备响应延迟时未能加载内容，请手动检查设备端！")
        return 0
    
    if len(items) ==0:
        # 确认的真实空目录
        with open(marker_file, "w") as f:
            f.write("该目录确认在设备上为空")
        return 0
    """
    # 遍历当前层级的所有项
    for item in items :
        if copied >= max_files:
            break
        
        # 文件夹处理
        if item.IsFolder:
            time.sleep(0.5)
            # ▨ 跳过隐藏文件夹
            if is_hidden_folder(item):
                print(f"[跳过隐藏] {item.Name}")
                continue

            # ▨ 递归处理子文件夹
            subfolder = item.GetFolder
            sub_local_dir = os.path.join(local_base_dir, item.Name)
            print(f"进入目录: {item.Name} → 本地路径: {sub_local_dir}")
            copied += copy_mtp_folder(subfolder, sub_local_dir, max_files - copied)
        
        #文件处理
        else:
            # ▨ 处理单个文件（本地不存在时复制）
            local_path = os.path.join(local_base_dir, item.Name)
            if os.path.exists(local_path):
                print(f"[已存在] {item.Name}")
                continue
            
            try:
                local_namespace.CopyHere(item)  # 4 | 16 无UI+自动重命名
                copied += 1
                print(f"[复制] {copied} 文件: {item.Name}")
            except Exception as e:
                print(f"❗ 复制失败: {item.Name} ({e})")
    print(f"目录 {mtp_namespace} 完成，复制文件数: {copied}")
    return copied


# 生成空目录报告
def generate_report():
    """生成空目录报告"""
    print("\n=== 目录完整性报告 ===")
    if not suspicious_folders:
        return
    
    print("\n⚠️ 需要验证的可能错误空目录:")
    for path in suspicious_folders:
        print(f" - {path}")
    
    # 可选：导出到日志文件
    with open("suspicious_folders.log", "w") as f:
        f.write("\n".join(suspicious_folders))

if __name__ == "__main__":
    backup_qq_photos_test()
    generate_report()
