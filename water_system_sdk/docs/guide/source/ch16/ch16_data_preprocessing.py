import pandas as pd
import numpy as np

# This is a simple way to make the SDK accessible to the script.
# A proper setup would involve installing the package.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.preprocessing.data_processor import Pipeline, DataCleaner, UnitConverter

def run_preprocessing():
    """
    This script demonstrates how to use a data processing pipeline to clean
    and transform a raw time series dataset.
    """
    # 1. 创建一份不完美的原始数据
    # 使用 pandas 创建一个带时间戳索引的 DataFrame
    time_index = pd.to_datetime(['2023-01-01 00:00', '2023-01-01 01:00', '2023-01-01 02:00',
                                 '2023-01-01 03:00', '2023-01-01 04:00', '2023-01-01 05:00'])
    raw_data = pd.DataFrame({
        'Rainfall_in': [0.1, 0.5, np.nan, 1.2, 0.8, np.nan], # 包含缺失值 (NaN)
        'Temperature_F': [45, 47, 48, 46, 44, 43]
    }, index=time_index)

    print("--- 原始数据 ---")
    print(raw_data)

    # 2. 定义数据处理管道
    # 步骤1：填充缺失值。我们使用 'ffill' 策略 (forward-fill)。
    cleaner = DataCleaner(strategy='ffill')

    # 步骤2：单位转换。我们只转换降雨列，从英寸到毫米。
    # 1 inch = 25.4 mm
    unit_converter = UnitConverter(scale_factor=25.4, columns=['Rainfall_in'])

    # 创建管道，并定义处理顺序
    processing_pipeline = Pipeline(processors=[cleaner, unit_converter])

    # 3. 运行管道
    processed_data = processing_pipeline.process(raw_data)

    # 为了清晰，重命名列
    processed_data = processed_data.rename(columns={'Rainfall_in': 'Rainfall_mm'})

    print("\n--- 处理后的数据 ---")
    print(processed_data)

    # 验证
    assert not processed_data['Rainfall_mm'].isnull().any(), "验证失败：仍有缺失值"
    # 验证第二个值是否被正确转换: 0.5 * 25.4 = 12.7
    assert abs(processed_data['Rainfall_mm'].iloc[1] - 12.7) < 1e-6, "验证失败：单位转换不正确"
    print("\n验证成功！")


if __name__ == "__main__":
    run_preprocessing()
