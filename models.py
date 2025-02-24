import sys
from pydantic import BaseModel, ValidationError, constr, conint, validator
from typing import Any, Dict, Literal, Optional, Union

class Announce(BaseModel):
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    info_hash: constr(min_length=20, max_length=2000, strict=True) = None
    peer_id:  Optional[constr(min_length=20, max_length=20, strict=True)]
    no_peer_id: Optional[conint(ge=0, le=1)] = 0
    key: Optional[str] = None
    port: conint(ge=0, le=65535)
    ipv6port: None
    downloaded: conint(ge=0, le=sys.maxsize)
    uploaded: conint(ge=0, le=sys.maxsize)
    left: conint(ge=0, le=sys.maxsize)
    passkey: Optional[str] = None
    event: Optional[Literal["started", "stopped", "completed"]] = ""
    numwant: Optional[conint(ge=0, le=sys.maxsize)] = 150
    compact: Optional[conint(ge=0, le=1)] = 0

class AnnounceResponse(BaseModel):
    failure_reason: Optional[str] = None
    warning_message: Optional[str] = None
    interval: Optional[conint(ge=0, le=sys.maxsize)] = None
    min_interval: Optional[conint(ge=0, le=sys.maxsize)] = None
    complete: Optional[conint(ge=0, le=sys.maxsize)] = None
    incomplete: Optional[conint(ge=0, le=sys.maxsize)] = None
    peers: Optional[Union[dict, bytes]] = None
    tracker_id: Optional[constr(min_length=6, max_length=20, strict=True)] = None

    #it makes sense that the request has underscores...
    #so why not the response too?
    def dict(self, *args, **kwargs):
        original_dict = super().dict(*args, **kwargs)
        return {k.replace('_', ' '): v for k, v in original_dict.items() if v}

    #as per spec, if failure reason is given no other responses will be given
    @validator('failure_reason', pre=True, always=True)
    def check_failure_reason(cls, v, values):
        if v is not None:
            values['warning_message'] = None
            values['interval'] = None
            values['min_interval'] = None
            values['complete'] = None
            values['incomplete'] = None
            values['peers'] = None
        return v

class ScrapeResult(BaseModel):
    complete: conint(ge=0) 
    downloaded: conint(ge=0)
    incomplete: conint(ge=0)

class ScrapeResponse(BaseModel):
    flags: Dict[str, Any]
    results: Dict[str, ScrapeResult]