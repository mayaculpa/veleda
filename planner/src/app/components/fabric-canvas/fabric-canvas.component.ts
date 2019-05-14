import { Component, OnInit, ViewChild, ElementRef, AfterViewInit, OnDestroy } from '@angular/core';
import { fabric } from 'fabric';
import { fromEvent, Subject } from 'rxjs';
import { takeUntil, debounceTime } from 'rxjs/operators';
import { FabricCanvasAspectService } from '../../services/fabric-canvas-aspect.service';

@Component({
  selector: 'app-fabric-canvas',
  templateUrl: './fabric-canvas.component.html',
  styleUrls: ['./fabric-canvas.component.css']
})
export class FabricCanvasComponent implements OnInit, AfterViewInit, OnDestroy {
  canvas: fabric.Canvas;

  // Used to resize the canvas object
  @ViewChild('canvasContainer') canvasContainer: ElementRef;
  private resizeWindow$ = fromEvent(window, 'resize');

  // Used to unsubscribe all subscriptions in the pipe operator
  private ngUnsubscribe$ = new Subject<void>();

  constructor(private fabricCanvasAspectService: FabricCanvasAspectService) {}

  ngOnInit() {
    this.canvas = new fabric.Canvas('canvas');
    this.canvas.backgroundColor = 'lightgreen';
    this.canvas.renderAll();

    // Update the canvas to match the container size
    this.resizeWindow$
      .pipe(
        debounceTime(300),
        takeUntil(this.ngUnsubscribe$)
      )
      .subscribe(() => {
        this.canvas.setDimensions({
          width: this.canvasContainer.nativeElement.offsetWidth,
          height: this.canvasContainer.nativeElement.offsetHeight
        });
      });

    // Add all existing fabric objects
    this.fabricCanvasAspectService.getAllFabricObjects().forEach(object => this.canvas.add(object));

    // When Fabric objects are added / removed, update the canvas
    this.fabricCanvasAspectService.addedFabricObjects$
      .pipe(takeUntil(this.ngUnsubscribe$))
      .subscribe(objects => objects.map(object => this.canvas.add(object)));
    // this.fabricCanvasAspectService.removedFabricObjects$
    //   .pipe(takeUntil(this.ngUnsubscribe$))
    //   .subscribe(objects => objects.map(object => this.canvas.remove(object)));
  }

  ngAfterViewInit() {
    // Sets the canvas dimensions during the initial render
    this.canvas.setDimensions({
      width: this.canvasContainer.nativeElement.offsetWidth,
      height: this.canvasContainer.nativeElement.offsetHeight
    });
  }

  ngOnDestroy() {
    this.ngUnsubscribe$.next();
    this.ngUnsubscribe$.complete();
  }
}
