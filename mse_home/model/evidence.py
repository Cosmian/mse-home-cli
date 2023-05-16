"""mse_home.model.evidence module."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.types import PUBLIC_KEY_TYPES
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_public_key,
)
from cryptography.x509 import (
    Certificate,
    CertificateRevocationList,
    load_pem_x509_certificate,
    load_pem_x509_crl,
)
from pydantic import BaseModel


class ApplicationEvidence(BaseModel):
    """Definition of an enclave evidence."""

    ratls_certificate: Certificate

    root_ca_crl: CertificateRevocationList

    pck_platform_crl: CertificateRevocationList

    pck_processor_crl: CertificateRevocationList

    tcb_info: Optional[Tuple[Tuple[Certificate, Certificate], Dict[str, Any]]]

    signer_pk: PUBLIC_KEY_TYPES

    class Config:
        """Overwrite internal structure."""

        arbitrary_types_allowed = True

    @staticmethod
    def load(path: Path):
        """Load the evidence from a json file."""
        with open(path, encoding="utf8") as f:
            dataMap = json.load(f)

            return ApplicationEvidence(
                ratls_certificate=load_pem_x509_certificate(
                    dataMap["ratls_certificate"].encode("utf-8")
                ),
                root_ca_crl=load_pem_x509_crl(dataMap["root_ca_crl"].encode("utf-8")),
                pck_platform_crl=load_pem_x509_crl(
                    dataMap["pck_platform_crl"].encode("utf-8")
                ),
                pck_processor_crl=load_pem_x509_crl(
                    dataMap["pck_processor_crl"].encode("utf-8")
                ),
                tcb_info=None,
                signer_pk=load_pem_public_key(
                    dataMap["signer_pk"].encode("utf-8"),
                ),
            )

    def save(self, path: Path) -> None:
        """Save the evidence into a json file."""
        with open(path, "w", encoding="utf8") as f:
            dataMap: Dict[str, Any] = {
                "ratls_certificate": self.ratls_certificate.public_bytes(
                    encoding=Encoding.PEM
                ).decode("utf-8"),
                "root_ca_crl": self.root_ca_crl.public_bytes(
                    encoding=Encoding.PEM,
                ).decode("utf-8"),
                "pck_platform_crl": self.pck_platform_crl.public_bytes(
                    encoding=Encoding.PEM,
                ).decode("utf-8"),
                "pck_processor_crl": self.pck_processor_crl.public_bytes(
                    encoding=Encoding.PEM,
                ).decode("utf-8"),
                "tcb_info": self.tcb_info,  # TODO
                "signer_pk": self.signer_pk.public_bytes(
                    encoding=Encoding.PEM,
                    format=PublicFormat.SubjectPublicKeyInfo,
                ).decode("utf-8"),
            }

            json.dump(dataMap, f, indent=4)
