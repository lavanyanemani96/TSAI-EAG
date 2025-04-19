from mcp.server.fastmcp import FastMCP
import math
import sys
import os

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models import AddInput, AddOutput, SqrtInput, SqrtOutput, StringsToIntsInput, StringsToIntsOutput, ExpSumInput, ExpSumOutput
from models import AddListInput, AddListOutput, FibonacciNumbersInput, FibonacciNumbersOutput, EmailResultInput, EmailResultOutput

# instantiate an MCP server client
mcp = FastMCP("Calculator")

@mcp.tool()
def add(input: AddInput) -> AddOutput:
    """Add two values"""
    print("CALLED: add(AddInput) -> AddOutput")
    return AddOutput(result=input.a + input.b)

@mcp.tool()
def add_list(input: AddListInput) -> AddListOutput:
    """Add all numbers in a list"""
    print("CALLED: add_list(AddListInput) -> AddListOutput")
    return AddListOutput(result=sum(input.l))

@mcp.tool()
def sqrt(input: SqrtInput) -> SqrtOutput:
    """Square root of a number"""
    print("CALLED: sqrt(SqrtInput) -> SqrtOutput")
    return SqrtOutput(result=input.a ** 0.5)

@mcp.tool()
def fibonacci_numbers(input: FibonacciNumbersInput) -> FibonacciNumbersOutput:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(FibonacciNumbersInput) -> FibonacciNumbersOutput")
    if input.n <= 0:
        return FibonacciNumbersOutput(l=[])
    fib_sequence = [0, 1]
    for _ in range(2, input.n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return FibonacciNumbersOutput(l=fib_sequence[:input.n])

@mcp.tool()
def strings_to_chars_to_int(input: StringsToIntsInput) -> StringsToIntsOutput:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(StringsToIntsInput) -> StringsToIntsOutput")
    ascii_values = [ord(char) for char in input.string]
    return StringsToIntsOutput(ascii_values=ascii_values)

@mcp.tool()
def int_list_to_exponential_sum(input: ExpSumInput) -> ExpSumOutput:
    """Return sum of exponentials of numbers in the list input.int_list"""
    print("CALLED: int_list_to_exponential_sum(ExpSumInput) -> ExpSumOutput")
    result = sum(math.exp(i) for i in input.int_list)
    return ExpSumOutput(result=result)

@mcp.tool()
def email_result(input: EmailResultInput) -> EmailResultOutput:
    """Send an email using input.recipient_email and include input.answer as the result."""

    recipient_email = input.recipient_email
    result = str(input.answer)
    
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'lavanyanemani96@gmail.com'
    sender_password = os.getenv("GMAIL_APP_PASSWORD")  # Use an app password for Gmail
    subject = "Agentic AI Result"
    body = f"Automated Agentic AI result: {result}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return EmailResultOutput(status=f"Email successfully sent to {recipient_email}")
    except Exception as e:
        return EmailResultOutput(status=f"Failed to send email: {e}")

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
