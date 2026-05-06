// Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

using System;

namespace SampleApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("========================================");
            Console.WriteLine("   WINBUILD CLOUD: SAMPLE .NET APP      ");
            Console.WriteLine("========================================");
            Console.WriteLine($"Current Time: {DateTime.Now}");
            Console.WriteLine($"Machine Name: {Environment.MachineName}");
            Console.WriteLine($"OS Version: {Environment.OSVersion}");
            Console.WriteLine("========================================");
            Console.WriteLine("Build Success Validation: OK");
            Console.WriteLine("Hello from a Windows Container!");
        }
    }
}
