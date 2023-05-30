"""mse_home.model.evidence module."""

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
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

    tcb_info: bytes

    tcb_cert: Certificate

    signer_pk: PublicKeyTypes

    class Config:
        """Overwrite internal structure."""

        arbitrary_types_allowed = True

    @property
    def collaterals(
        self,
    ) -> Tuple[
        bytes, Certificate, CertificateRevocationList, CertificateRevocationList
    ]:
        """Return the PCCS collaterals."""
        return (self.tcb_info, self.tcb_cert, self.root_ca_crl, self.pck_platform_crl)

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
                tcb_info=bytes.fromhex(dataMap["tcb_info"]),
                tcb_cert=load_pem_x509_certificate(dataMap["tcb_cert"].encode("utf-8")),
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
                "tcb_info": self.tcb_info.hex(),
                "tcb_cert": self.tcb_cert.public_bytes(encoding=Encoding.PEM).decode(
                    "utf-8"
                ),
                "signer_pk": self.signer_pk.public_bytes(
                    encoding=Encoding.PEM,
                    format=PublicFormat.SubjectPublicKeyInfo,
                ).decode("utf-8"),
            }

            json.dump(dataMap, f, indent=4)
