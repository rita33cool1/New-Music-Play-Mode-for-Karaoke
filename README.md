# New-Music-Play-Mode-for-Karaoke

We build a more flexible Karaoke system which can 
- create individual playlists.
- automatically recognize who is singing and play his own list.

In this project, I was responsible for the **Raspberry Pi** and the backend **AWS** services:
+ Controlling Raspberry Pi to get singers’ information like pictures.
+ Transferring data from the Raspberry Pi to the server in AWS cloud through *SNS/SQS* and *IoT core*.
+ Using *Rekognition* to recognize the singer and storing data in *S3*.
+ Programming in *Lambda* to automatically trigger recognition.
