# train_grpo.py
##這邊的dataset是原本預設的資料集，與我們需要的無關
#from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

#這是一個簡單粗暴的獎勵計算方式，誰越多不同字母誰就越高分
#dataset = load_dataset("trl-lib/ultrafeedback-prompt", split="train")
# Dummy reward function for demonstration purposes
def reward_num_unique_letters(completions, **kwargs):
    """Reward function that rewards completions with more unique letters."""
    completion_contents = [completion[0]["content"] for completion in completions]
    return [float(len(set(content))) for content in completion_contents]
#這邊就是訓練的code
training_args = GRPOConfig(output_dir="Qwen2-0.5B-GRPO")
trainer = GRPOTrainer(
    model="Qwen/Qwen2-0.5B-Instruct",#載入模型
    reward_funcs=reward_num_unique_letters,#載入獎勵，長得像這樣[31.0,41.0,..]
    args=training_args,#載入參數
    train_dataset=dataset,#載入資料集
    '''
    資料集實際內容呈現 呈現像這樣
    [[{'content': 'create a table with 5 meals per day for 2 days, this is prepared for a 20 year old female. \nit sould be vegan, i should not contain nuts.\nshow a table with the meal, description, calorie count \nshow it in this style:\nDay n\nMeal n: meal name\n\nn ingredient\nn ingredient\nn ingredient\nn calories','role': 'user'}],
    [{'content': 'In this task you will be given a list of integers. You should find the maximum absolute difference between 2 integers in the list. The absolute difference is the absolute value of one integer subtracted by another. The output should be a single integer which is the largest possible absolute distance.\nQ: [31, 28, -27]\nA: '
    'role': 'user'}],...
   ''')
trainer.train()#開始訓練
#訓練用 accelerate launch train_grpo.py