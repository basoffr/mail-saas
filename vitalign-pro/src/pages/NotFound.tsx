import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Home, ArrowLeft } from "lucide-react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-gradient-subtle flex items-center justify-center p-6">
      <Card className="p-12 text-center max-w-md shadow-card rounded-2xl">
        <div className="space-y-6">
          <div className="mx-auto w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center">
            <span className="text-4xl font-bold text-primary">404</span>
          </div>
          
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">Page Not Found</h1>
            <p className="text-muted-foreground">
              Sorry, the page you're looking for doesn't exist or has been moved.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <Button asChild className="bg-gradient-primary hover:shadow-glow">
              <Link to="/leads">
                <Home className="w-4 h-4 mr-2" />
                Go to Leads
              </Link>
            </Button>
            <Button variant="outline" onClick={() => window.history.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default NotFound;