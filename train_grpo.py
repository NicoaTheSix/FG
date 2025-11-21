# train_grpo.py
##這邊的dataset是原本預設的資料集，與我們需要的無關
#from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

def loadDataset():
    return
def loadReward():
    return

training_args = GRPOConfig(output_dir="Qwen2-0.5B-GRPO")
trainer = GRPOTrainer(
    model="Qwen/Qwen2-0.5B-Instruct",#改成另一個模型
    reward_funcs=loadReward(),#改成自己的
    args=training_args,
    train_dataset=loadDataset()#改成自己的
)
trainer.train()#