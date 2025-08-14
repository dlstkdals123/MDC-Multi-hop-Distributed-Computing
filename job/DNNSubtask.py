import torch

from job import SubtaskInfo, DNNOutput

class DNNSubtask:
    """
    서브태스크 정보와 모델 및 계산량, 전송량을 저장하는 클래스입니다.

    Attributes:
        _subtask_info (SubtaskInfo): 서브태스크 정보.
        _dnn_model (torch.nn.Module): 실제 모델.
        _computing_capacity (float): 모델의 계산량 (GFLOPs).
        _transfer_capacity (float): 전송량 (KB).
    """
    def __init__(self, subtask_info: SubtaskInfo, dnn_model: torch.nn.Module, computing_capacity: float, transfer_capacity: float):
        self._subtask_info = subtask_info
        self._dnn_model = dnn_model

        self._computing_capacity = computing_capacity
        self._transfer_capacity = transfer_capacity

        self._remaining_computing_capacity = computing_capacity
        self._remaining_transfer_capacity = transfer_capacity

    @property
    def subtask_info(self) -> SubtaskInfo:
        return self._subtask_info
    
    def get_total_capacity(self) -> float:
        """
        서브태스크가 계산일 경우 계산량을 반환합니다. (GFLOPs)
        서브태스크가 전송일 경우 전송량을 반환합니다. (KB)

        노드의 총 계산량 또는 전송량을 계산하기 위해 사용됩니다.
        """
        return self._computing_capacity if self._subtask_info.is_computing() else self._transfer_capacity

    def get_backlog(self) -> float:
        """
        서브태스크의 백로그를 반환합니다. (GFLOPs or KB)

        서브태스크의 남은 계산량 또는 전송량을 반환합니다.
        이는 Virtual Queue Backlog 계산에 사용됩니다.
        """
        return self._remaining_computing_capacity if self._subtask_info.is_computing() else self._remaining_transfer_capacity
    
    def run(self, input: torch.Tensor) -> torch.Tensor:
        """
        data를 입력으로 받아, 서브태스크를 실행합니다.
        서브태스크가 계산일 경우 모델을 계산합니다.
        전송일 경우 데이터를 그대로 반환합니다.

        Args:
            data (torch.Tensor): 서브태스크의 입력 데이터.

        Returns:
            DNNOutput: 서브태스크의 출력. (서브태스크가 계산일 경우 모델 계산 결과, 전송일 경우 그대로 반환)
        """
        if self._subtask_info.is_computing():
            with torch.no_grad():
                output = self._dnn_model(input)

            if isinstance(output, list):
                output = [o.to("cpu") for o in output]
            else:
                output = output.to("cpu")
        
        return output

    def decrease_backlog(self, amount: float):
        """
        서브태스크의 백로그를 감소시킵니다. (GFLOPs or KB)

        Args:
            amount (float): 감소시킬 백로그 양.
        """
        if self._subtask_info.is_computing():
            self._remaining_computing_capacity = max(self._remaining_computing_capacity - amount, 0)
        else:
            self._remaining_transfer_capacity = max(self._remaining_transfer_capacity - amount, 0)