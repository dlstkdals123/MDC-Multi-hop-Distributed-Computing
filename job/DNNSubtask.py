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

    @property
    def subtask_info(self) -> SubtaskInfo:
        return self._subtask_info
    
    def get_backlog(self) -> float:
        """
        서브태스크가 계산일 경우 계산량을 반환합니다. (GFLOPs)
        서브태스크가 전송일 경우 전송량을 반환합니다. (KB)
        """
        return self._computing_capacity if self._subtask_info.is_computing() else self._transfer_capacity
    
    def run(self, data: torch.Tensor) -> DNNOutput:
        """
        data를 입력으로 받아, 서브태스크를 실행합니다.
        서브태스크가 계산일 경우 모델을 계산하고, 전송일 경우 데이터를 복사하여 DNNOutput 객체를 생성합니다.

        Args:
            data (torch.Tensor): 서브태스크의 입력 데이터.

        Returns:
            DNNOutput: 서브태스크의 출력. (서브태스크가 계산일 경우 모델 계산 결과, 전송일 경우 복사된 데이터)
        """
        if self._subtask_info.is_transmission():
            # 단순히 데이터를 복사하여 DNNOutput 객체를 생성합니다.
            if isinstance(data, list):
                data = [d.to("cpu") for d in data]
            else:
                data = data.to("cpu")

            dnn_output = DNNOutput(data, self._subtask_info)
        else:
            # 모델 계산
            with torch.no_grad():
                output: torch.Tensor = self._dnn_model(data)

            if isinstance(output, list):
                output = [o.to("cpu") for o in output]
            else:
                output = output.to("cpu")

            dnn_output = DNNOutput(output, self._subtask_info)
        
        return dnn_output