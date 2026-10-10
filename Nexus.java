
import java.util.ArrayList;
import java.util.Scanner;

public class Nexus {

    static Scanner sc = new Scanner(System.in);

    static ArrayList<String> customers = new ArrayList<>();
    static ArrayList<String> campaigns = new ArrayList<>();
    static ArrayList<String> webinars = new ArrayList<>();
    static ArrayList<String> subscriptions = new ArrayList<>();

    static void dashboard() {
        System.out.println("\n===== NEXUS DASHBOARD =====");
        System.out.println("Total Customers: " + customers.size());
        System.out.println("Total Campaigns: " + campaigns.size());
        System.out.println("Total Webinars: " + webinars.size());
        System.out.println("Total Subscriptions: " + subscriptions.size());
    }

    static void addCustomer() {
        System.out.print("Enter customer name: ");
        String name = sc.nextLine();

        System.out.print("Enter customer email: ");
        String email = sc.nextLine();

        customers.add(name + " | " + email);
        System.out.println("Customer added successfully!");
    }

    static void viewCustomers() {
        System.out.println("\n===== CRM CUSTOMERS =====");

        if (customers.isEmpty()) {
            System.out.println("No customers found.");
        } else {
            for (String customer : customers) {
                System.out.println(customer);
            }
        }
    }

    static void createCampaign() {
        System.out.print("Enter campaign name: ");
        String name = sc.nextLine();

        campaigns.add(name + " (Pending Approval)");
        System.out.println("Campaign created. Approval is required before launch.");
    }

    static void scheduleWebinar() {
        System.out.print("Enter webinar name: ");
        String name = sc.nextLine();

        System.out.print("Enter webinar date: ");
        String date = sc.nextLine();

        webinars.add(name + " | Date: " + date);
        System.out.println("Webinar scheduled successfully!");
    }

    static void addSubscription() {
        System.out.print("Enter customer name: ");
        String name = sc.nextLine();

        System.out.print("Enter subscription plan: ");
        String plan = sc.nextLine();

        subscriptions.add(name + " | Plan: " + plan);
        System.out.println("Subscription added successfully!");
    }

    static void viewList(String title, ArrayList<String> list) {
        System.out.println("\n===== " + title + " =====");

        if (list.isEmpty()) {
            System.out.println("No records found.");
        } else {
            for (String item : list) {
                System.out.println(item);
            }
        }
    }

    static void aiAgent() {
        System.out.println("\n===== NEXUS AI AGENT =====");
        System.out.println("Try: show customers");
        System.out.println("Try: show campaigns");
        System.out.println("Try: show webinars");
        System.out.println("Try: launch campaign");
        System.out.print("Enter your instruction: ");

        String command = sc.nextLine().toLowerCase();

        if (command.contains("show") && command.contains("customer")) {
            viewCustomers();
        } else if (command.contains("show") && command.contains("campaign")) {
            viewList("CAMPAIGNS", campaigns);
        } else if (command.contains("show") && command.contains("webinar")) {
            viewList("WEBINARS", webinars);
        } else if (command.contains("launch") && command.contains("campaign")) {
            System.out.println("Approval required before launching a campaign.");
            System.out.print("Approve launch? (yes/no): ");

            String approval = sc.nextLine();

            if (approval.equalsIgnoreCase("yes")) {
                System.out.println("Demo approval recorded.");
                System.out.println("Connect a marketing service to launch a real campaign.");
            } else {
                System.out.println("Campaign launch cancelled.");
            }
        } else {
            System.out.println("Command not recognized. Try another instruction.");
        }
    }

    public static void main(String[] args) {

        int choice;

        do {
            System.out.println("\n========== NEXUS PLATFORM ==========");
            System.out.println("1. Dashboard");
            System.out.println("2. Add Customer");
            System.out.println("3. View Customers");
            System.out.println("4. Create Marketing Campaign");
            System.out.println("5. Schedule Webinar");
            System.out.println("6. Add Subscription");
            System.out.println("7. View Campaigns");
            System.out.println("8. View Webinars");
            System.out.println("9. View Subscriptions");
            System.out.println("10. AI Agent");
            System.out.println("0. Exit");
            System.out.print("Enter your choice: ");

            while (!sc.hasNextInt()) {
                System.out.println("Please enter a number.");
                sc.nextLine();
            }

            choice = sc.nextInt();
            sc.nextLine();

            switch (choice) {
                case 1:
                    dashboard();
                    break;
                case 2:
                    addCustomer();
                    break;
                case 3:
                    viewCustomers();
                    break;
                case 4:
                    createCampaign();
                    break;
                case 5:
                    scheduleWebinar();
                    break;
                case 6:
                    addSubscription();
                    break;
                case 7:
                    viewList("CAMPAIGNS", campaigns);
                    break;
                case 8:
                    viewList("WEBINARS", webinars);
                    break;
                case 9:
                    viewList("SUBSCRIPTIONS", subscriptions);
                    break;
                case 10:
                    aiAgent();
                    break;
                case 0:
                    System.out.println("Thank you for using Nexus!");
                    break;
                default:
                    System.out.println("Invalid choice. Try again.");
            }

        } while (choice != 0);

        sc.close();
    }
}
