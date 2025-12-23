from fastapi import APIRouter
import numpy as np
from utils.qlearning import Q, states, ACTIONS

router = APIRouter()

@router.get("/policy/")
def best_policy():
    policy = {state: ACTIONS[int(np.argmax(Q[i]))] for i, state in enumerate(states)}
    return {"best_policy": policy, "Q_shape": Q.shape}
