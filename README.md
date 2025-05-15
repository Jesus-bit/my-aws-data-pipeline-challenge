From: Baz Foobar <baz@artefact.com>  
To: Alice Smith <alice@artefact.com>  
Subject: Re: [Request] Data Ingestion with AWS  

Hi Alice,

Thanks for the detailed request! Here's how I propose to build the pipeline:

✅ A Lambda function will fetch the data from the Galactic Services API (`https://swapi.info/people`) and save the raw JSON with timestamp into the `raw/` folder of an S3 bucket.

✅ A Glue Studio Job will be triggered manually or via schedule, which:
- Extracts relevant fields
- Normalizes birth years
- Converts mass to pounds
- Applies filters and data cleaning rules
- Outputs a clean CSV to the `processed/` folder

🗂️ All the code is included in the `src/` folder in this repository. A diagram and implementation notes can be found in `README.md`.

🕒 For automation, I recommend using EventBridge rules or Step Functions to orchestrate the Lambda → Glue execution daily.

🚀 Bonus: I’ve included a Terraform file (in `iac/`) that can deploy or destroy this pipeline in your AWS environment.

Let me know if anything needs adjusting or if you'd like a demo!

Cheers,  
Baz




+--------------+       +----------+       +------------+       +-------------+
|   API swapi  | ----> |  Lambda  | ----> | S3 /raw/   | ----> |  Glue Job   |
+--------------+       +----------+       +------------+       +-------------+
                                                             |
                                                             v
                                                        S3 /processed/

![Diagrama del pipeline](draw.jpg)
