# SPDX-FileCopyrightText: 2025 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""openai_gateway"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

from .exceptions import PDFTitleException

logger = logging.getLogger(__name__)

load_dotenv()

__OPENAI_CLIENT = None

try:
    from openai import OpenAI, OpenAIError

    try:
        __OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except OpenAIError:
        pass
except ImportError:
    logger.warning("openai package is not available")


def get_title_from_openai(
    pdf_data: bytes, openai_model: str, openai_show_usage: bool
) -> Optional[str]:
    """ask OpenAI the title"""
    if __OPENAI_CLIENT is None:
        raise PDFTitleException(
            "OpenAI support is not ready, is openai package installed and OPENAI_API_KEY set ?"
        )

    file_object = None
    try:
        file_object = __OPENAI_CLIENT.files.create(
            file=("pdftitle.arg.pdf", pdf_data), purpose="assistants"
        )
        logger.debug(file_object)
        assistant = __OPENAI_CLIENT.beta.assistants.create(
            name="",
            instructions="You are an assistant that can process PDF files.",
            model=openai_model,
            tools=[{"type": "file_search"}],
        )
        logger.debug(assistant)
        thread = __OPENAI_CLIENT.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": "What is the title of this PDF document ? "
                    + "Please do your best and find a title "
                    + "even if you are not sure and "
                    + "please respond with the title only.",
                    "attachments": [
                        {"file_id": file_object.id, "tools": [{"type": "file_search"}]}
                    ],
                }
            ]
        )
        logger.debug(thread)
        run = __OPENAI_CLIENT.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant.id
        )
        logger.debug(run)
        messages = list(
            __OPENAI_CLIENT.beta.threads.messages.list(
                thread_id=thread.id, run_id=run.id
            )
        )
        logger.debug(messages)
        message_content = messages[0].content[0].text
        # replace annotations to get a human readable text
        for _, annotation in enumerate(message_content.annotations):
            message_content.value = message_content.value.replace(annotation.text, "")

        if openai_show_usage:
            print(
                f"Completion: {run.usage.completion_tokens}, "
                + "Prompt: {run.usage.prompt_tokens}, "
                + "Total: {run.usage.total_tokens} tokens"
            )
        return message_content.value
    finally:
        if file_object is not None:
            __OPENAI_CLIENT.files.delete(file_object.id)
